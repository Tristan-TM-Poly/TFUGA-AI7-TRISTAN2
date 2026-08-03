from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_ci_proof_t.r03.conflicts import EvidenceConflictEngine
from omega_ci_proof_t.r03.debt import ProofDebtEngine
from omega_ci_proof_t.r03.experiments import ExperimentAllocator, candidates_from_mapping
from omega_ci_proof_t.r03.graph import EpistemicGraphEngine
from omega_ci_proof_t.r03.models import EpistemicEdge, EpistemicNode, TruthSLO
from omega_ci_proof_t.r03.oak import run_oakbench
from omega_ci_proof_t.r03.slo import TruthSLOEngine, slos_from_mapping

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "omega_ci_proof_t"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def engine() -> EpistemicGraphEngine:
    return EpistemicGraphEngine.from_mapping(load("r03-graph.json"))


def test_node_rejects_unknown_kind():
    with pytest.raises(ValueError):
        EpistemicNode("X", "magic", "x")


def test_node_rejects_bad_criticality():
    with pytest.raises(ValueError):
        EpistemicNode("X", "claim", "x", criticality=6)


def test_edge_rejects_self_loop():
    with pytest.raises(ValueError):
        EpistemicEdge("A", "A", "depends_on")


def test_graph_identity_is_deterministic():
    raw = load("r03-graph.json")
    a = EpistemicGraphEngine.from_mapping(raw).graph.graph_id
    raw["nodes"] = list(reversed(raw["nodes"]))
    raw["edges"] = list(reversed(raw["edges"]))
    b = EpistemicGraphEngine.from_mapping(raw).graph.graph_id
    assert a == b


def test_graph_rejects_duplicate_nodes():
    raw = load("r03-graph.json")
    raw["nodes"].append(dict(raw["nodes"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        EpistemicGraphEngine.from_mapping(raw)


def test_graph_rejects_unknown_edge_endpoint():
    raw = load("r03-graph.json")
    raw["edges"].append({"source": "CLAIM-REPOTWIN-DETERMINISTIC", "target": "MISSING", "relation": "depends_on"})
    with pytest.raises(ValueError, match="unknown node"):
        EpistemicGraphEngine.from_mapping(raw)


def test_graph_rejects_dependency_cycle():
    raw = {"nodes": [{"node_id": "A", "kind": "claim", "label": "A"}, {"node_id": "B", "kind": "claim", "label": "B"}], "edges": [{"source": "A", "target": "B", "relation": "depends_on"}, {"source": "B", "target": "A", "relation": "depends_on"}]}
    with pytest.raises(ValueError, match="cycle"):
        EpistemicGraphEngine.from_mapping(raw)


def test_graph_stats_are_typed_and_non_mutating():
    stats = engine().stats()
    assert stats["nodes_by_kind"]["claim"] == 4
    assert stats["remote_mutations"] == 0


def test_invalidation_propagates_from_evidence_to_claim():
    result = engine().invalidate(["EVID-EXPIRY-FIXTURE"])
    assert "CLAIM-EVIDENCE-EXPIRY" in result.invalidated_node_ids


def test_invalidation_propagates_through_claim_dependency():
    result = engine().invalidate(["EVID-EXPIRY-FIXTURE"])
    assert "CLAIM-CLAIM-COVERAGE" in result.invalidated_node_ids


def test_invalidation_keeps_path_receipt():
    result = engine().invalidate(["EVID-EXPIRY-FIXTURE"])
    assert result.propagation_paths["CLAIM-CLAIM-COVERAGE"] == (
        "EVID-EXPIRY-FIXTURE", "CLAIM-EVIDENCE-EXPIRY", "CLAIM-CLAIM-COVERAGE"
    )


def test_invalidation_rejects_unknown_trigger():
    with pytest.raises(KeyError):
        engine().invalidate(["UNKNOWN"])


def test_contradiction_does_not_automatically_invalidate_claim():
    result = engine().invalidate(["COUNTER-ROUTER-DYNAMIC"])
    assert "CLAIM-ROUTER-CONSERVATIVE" not in result.invalidated_node_ids


def test_conflict_engine_detects_support_and_counterevidence():
    report = EvidenceConflictEngine().analyze(engine())
    assert report.open_conflicts == 1
    assert report.conflicts[0].claim_id == "CLAIM-ROUTER-CONSERVATIVE"


def test_conflict_report_proposes_discriminating_experiment():
    report = EvidenceConflictEngine().analyze(engine())
    assert "EXP-ROUTER-DYNAMIC-FIXTURE" in report.conflicts[0].discriminating_experiments


def test_baseline_proof_debt_is_bounded_and_noncritical():
    report = ProofDebtEngine().evaluate(engine(), load("r03-state.json"))
    assert report.total_score == 3.0
    assert report.critical_open == 0
    assert report.counts_by_category == {"evidence_conflict": 1}


def test_low_coverage_creates_debt():
    state = load("r03-state.json")
    state["claims"]["CLAIM-EVIDENCE-EXPIRY"]["coverage_score"] = 0.1
    report = ProofDebtEngine().evaluate(engine(), state)
    assert "low_claim_coverage" in report.counts_by_category


def test_stale_evidence_creates_debt():
    state = load("r03-state.json")
    state["claims"]["CLAIM-EVIDENCE-EXPIRY"]["evidence_statuses"] = ["STALE"]
    report = ProofDebtEngine().evaluate(engine(), state)
    assert "noncurrent_evidence" in report.counts_by_category


def test_invalidated_critical_evidence_creates_critical_debt():
    state = load("r03-state.json")
    state["claims"]["CLAIM-EVIDENCE-EXPIRY"]["evidence_statuses"] = ["INVALIDATED"]
    report = ProofDebtEngine().evaluate(engine(), state)
    assert report.critical_open >= 1


def test_missing_provenance_creates_debt():
    state = load("r03-state.json")
    state["claims"]["CLAIM-CLAIM-COVERAGE"]["provenance_complete"] = False
    report = ProofDebtEngine().evaluate(engine(), state)
    assert "missing_provenance" in report.counts_by_category


def test_open_critical_residual_creates_critical_debt():
    state = load("r03-state.json")
    state["residuals"] = [{"id": "R", "status": "OPEN", "severity": "critical", "claim_ids": ["CLAIM-ROUTER-CONSERVATIVE"]}]
    report = ProofDebtEngine().evaluate(engine(), state)
    assert report.critical_open == 1


def test_truth_slo_fixture_passes():
    eng = engine()
    state = load("r03-state.json")
    debt = ProofDebtEngine().evaluate(eng, state)
    report = TruthSLOEngine().evaluate(eng, state, debt, slos_from_mapping(load("r03-slos.json")))
    assert report.passed
    assert report.critical_failures == 0
    assert report.metrics["proof_debt_score"] == 3.0


def test_truth_slo_fails_for_stale_critical_claim():
    eng = engine()
    state = load("r03-state.json")
    state["claims"]["CLAIM-ROUTER-CONSERVATIVE"]["evidence_statuses"] = ["STALE"]
    debt = ProofDebtEngine().evaluate(eng, state)
    report = TruthSLOEngine().evaluate(eng, state, debt, slos_from_mapping(load("r03-slos.json")))
    assert not report.passed
    assert any(item.slo_id == "SLO-CRITICAL-CURRENT" and not item.passed for item in report.evaluations)


def test_truth_slo_rejects_unknown_metric():
    eng = engine()
    state = load("r03-state.json")
    debt = ProofDebtEngine().evaluate(eng, state)
    with pytest.raises(KeyError):
        TruthSLOEngine().evaluate(eng, state, debt, (TruthSLO("S", "unknown", ">=", 1, "critical", ""),))


def test_experiment_allocator_selects_best_safe_portfolio():
    portfolio = ExperimentAllocator().allocate(candidates_from_mapping(load("r03-experiments.json")), budget=1.0)
    assert [item.experiment_id for item in portfolio.selected] == ["EXP-ROUTER-DYNAMIC-FIXTURE", "EXP-REPOTWIN-CROSS-ENV"]
    assert portfolio.consumed_budget <= 1.0


def test_experiment_allocator_rejects_publish_capability():
    portfolio = ExperimentAllocator().allocate(candidates_from_mapping(load("r03-experiments.json")), budget=10.0)
    assert portfolio.rejected["EXP-PUBLISH-RESULTS"] == "sensitive capability is forbidden in A3"


def test_experiment_allocator_rejects_high_risk():
    portfolio = ExperimentAllocator().allocate(candidates_from_mapping(load("r03-experiments.json")), budget=10.0)
    assert "safety risk" in portfolio.rejected["EXP-HIGH-RISK"]


def test_experiment_allocator_never_authorizes_execution():
    portfolio = ExperimentAllocator().allocate(candidates_from_mapping(load("r03-experiments.json")), budget=1.0)
    payload = portfolio.to_dict()
    assert payload["execution_authorized"] is False
    assert payload["remote_mutations"] == 0


def test_experiment_allocator_rejects_negative_budget():
    with pytest.raises(ValueError):
        ExperimentAllocator().allocate((), budget=-1)


def test_oakbench_passes_and_preserves_a3():
    result = run_oakbench()
    assert result["passed"]
    assert result["maximum_authority"] == "A3"
    assert result["automatic_merge_allowed"] is False
    assert result["remote_mutations"] == 0
