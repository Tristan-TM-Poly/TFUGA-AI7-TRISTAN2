from __future__ import annotations

from .conflicts import EvidenceConflictEngine
from .debt import ProofDebtEngine
from .experiments import ExperimentAllocator
from .graph import EpistemicGraphEngine
from .models import ExperimentCandidate, TruthSLO
from .slo import TruthSLOEngine


def _fixture() -> tuple[EpistemicGraphEngine, dict[str, object]]:
    raw = {
        "nodes": [
            {"node_id": "CLAIM-A", "kind": "claim", "label": "A", "criticality": 5},
            {"node_id": "CLAIM-B", "kind": "claim", "label": "B", "criticality": 3},
            {"node_id": "EVID-A", "kind": "evidence", "label": "Evidence A"},
            {"node_id": "COUNTER-A", "kind": "counterevidence", "label": "Counter A"},
            {"node_id": "TEST-A", "kind": "test", "label": "Test A"},
        ],
        "edges": [
            {"source": "CLAIM-A", "target": "EVID-A", "relation": "supported_by"},
            {"source": "CLAIM-A", "target": "COUNTER-A", "relation": "contradicted_by"},
            {"source": "CLAIM-A", "target": "TEST-A", "relation": "verified_by"},
            {"source": "CLAIM-B", "target": "CLAIM-A", "relation": "depends_on"},
        ],
    }
    state = {
        "claims": {
            "CLAIM-A": {"coverage_score": 1.0, "coverage_threshold": 0.8, "required_tests": 1, "observed_tests": 1, "evidence_statuses": ["CURRENT"], "provenance_complete": True},
            "CLAIM-B": {"coverage_score": 0.5, "coverage_threshold": 0.8, "required_tests": 0, "observed_tests": 0, "evidence_statuses": ["STALE"], "provenance_complete": False},
        },
        "residuals": [],
        "conflicts": [{"claim_id": "CLAIM-A", "status": "OPEN", "severity": "critical"}],
    }
    return EpistemicGraphEngine.from_mapping(raw), state


def run_oakbench() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    engine, state = _fixture()
    checks.append({"name": "deterministic_graph_identity", "passed": engine.graph.graph_id == EpistemicGraphEngine.from_mapping(engine.graph.to_dict()).graph.graph_id})
    invalidation = engine.invalidate(["EVID-A"])
    checks.append({"name": "invalidation_propagates_to_claim_and_dependents", "passed": {"EVID-A", "CLAIM-A", "CLAIM-B"}.issubset(invalidation.invalidated_node_ids)})
    debt = ProofDebtEngine().evaluate(engine, state)
    checks.append({"name": "proof_debt_is_nonzero_for_stale_undercovered_claim", "passed": debt.total_score > 0 and debt.critical_open > 0})
    conflicts = EvidenceConflictEngine().analyze(engine)
    checks.append({"name": "conflict_detected_without_resolution_claim", "passed": conflicts.open_conflicts == 1})
    slos = (TruthSLO("SLO-CURRENT", "critical_claims_current_ratio", ">=", 1.0, "critical", ""),)
    slo_report = TruthSLOEngine().evaluate(engine, state, debt, slos)
    checks.append({"name": "truth_slo_uses_measured_metrics", "passed": slo_report.metrics["critical_claims_current_ratio"] == 1.0})
    candidates = (
        ExperimentCandidate("EXP-SAFE", "safe", 0.8, 0.2, 0.1, 0.0, ("CLAIM-A",)),
        ExperimentCandidate("EXP-MERGE", "forbidden", 1.0, 0.1, 0.0, 0.0, ("CLAIM-A",), "merge"),
    )
    portfolio = ExperimentAllocator().allocate(candidates, budget=1.0)
    checks.append({"name": "experiment_allocator_plans_but_denies_sensitive_authority", "passed": [item.experiment_id for item in portfolio.selected] == ["EXP-SAFE"] and "EXP-MERGE" in portfolio.rejected})
    cycle_rejected = False
    try:
        EpistemicGraphEngine.from_mapping({"nodes": [{"node_id": "A", "kind": "claim", "label": "A"}, {"node_id": "B", "kind": "claim", "label": "B"}], "edges": [{"source": "A", "target": "B", "relation": "depends_on"}, {"source": "B", "target": "A", "relation": "depends_on"}]})
    except ValueError:
        cycle_rejected = True
    checks.append({"name": "dependency_cycles_rejected", "passed": cycle_rejected})
    passed = all(bool(item["passed"]) for item in checks)
    return {
        "schema": "omega-ci-r03-oak/v3",
        "passed": passed,
        "checks": checks,
        "maximum_authority": "A3",
        "automatic_merge_allowed": False,
        "remote_mutations": 0,
        "scientific_validation_claimed": False,
    }
