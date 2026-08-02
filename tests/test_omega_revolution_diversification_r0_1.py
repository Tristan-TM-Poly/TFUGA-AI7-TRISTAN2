from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from omega_revolution_diversification_t import (
    ActionProposal,
    ActionSensitivity,
    ConductorDecision,
    DiscoveryCell,
    Evidence,
    EvidenceKind,
    FailureCase,
    Hypothesis,
    MMinusRule,
    OakStatus,
    QualityObservation,
    Quantity,
    RepositorySnapshot,
    RevolutionDiversificationCompiler,
    allocate_budget,
    audit_repository,
    build_demo_cells,
    canonical_ablation_fixture,
    canonical_raman_fixture,
    canonical_truth_audit_fixture,
    decide_quality,
    event_records_to_mminus,
    knowledge_cell_to_discovery_cell,
    registry_by_group,
    registry_payload,
    run_mminus_ablation,
    run_raman_loop,
    score_hypotheses,
    stable_id,
)
from omega_revolution_diversification_t.raman_loop import RamanModelKind
from omega_revolution_diversification_t.truth_audit import (
    BenchmarkObservation,
    DocumentationClaim,
    estimate_empirical_exponent,
)


def test_stable_id_is_deterministic_and_namespaced() -> None:
    first = stable_id("claim", {"b": 2, "a": 1})
    second = stable_id("claim", {"a": 1, "b": 2})
    assert first == second
    assert first.startswith("urn:omega:claim:")


def test_quantity_requires_unit_and_nonnegative_uncertainty() -> None:
    assert Quantity(1.0, "m", 0.1).validate() == []
    assert Quantity(1.0, "", -0.1).validate()


def test_hypothesis_requires_assumptions_and_falsification() -> None:
    hypothesis = Hypothesis(
        statement="x", domain="test", assumptions=(), falsification_conditions=(),
        value_potential=0.5, information_gain=0.5, falsifiability=0.5,
        reusability=0.5, cost=1, time_cost=1, operational_uncertainty=0.5,
        dependency_load=0.5,
    )
    errors = hypothesis.validate()
    assert any("assumption" in error for error in errors)
    assert any("falsification" in error for error in errors)


def test_action_requires_approval_for_sensitive_operations() -> None:
    action = ActionProposal(
        title="Publish", rationale="External disclosure",
        sensitivity=ActionSensitivity.HUMAN_APPROVAL_REQUIRED,
        reversible=False, expected_value=0.5,
    )
    assert any("approvals" in error for error in action.validate())


def test_promoted_cell_requires_result_and_baseline() -> None:
    hypothesis = Hypothesis(
        statement="candidate works", domain="test", assumptions=("fixture valid",),
        falsification_conditions=("metric fails",), value_potential=0.5,
        information_gain=0.5, falsifiability=0.5, reusability=0.5,
        cost=1, time_cost=1, operational_uncertainty=0.5, dependency_load=0.5,
    )
    cell = DiscoveryCell(
        title="candidate", domain="test", problem="problem", user="user",
        observable_pain="pain", current_baseline="baseline",
        hypotheses=[hypothesis], status=OakStatus.DEMONSTRATED,
    )
    errors = cell.validate()
    assert any("result evidence" in error for error in errors)
    assert any("baseline" in error for error in errors)


def test_demo_cells_are_valid_and_cover_three_fronts() -> None:
    cells = build_demo_cells()
    assert len(cells) == 3
    assert {cell.domain for cell in cells} == {"spectroscopy", "software-quality", "negative-memory"}
    assert all(cell.validate() == [] for cell in cells)


def test_registry_has_exact_8_by_8_structure() -> None:
    payload = registry_payload()
    groups = registry_by_group()
    assert payload["module_count"] == 64
    assert payload["group_count"] == 8
    assert all(len(modules) == 8 for modules in groups.values())
    assert len({module.name for modules in groups.values() for module in modules}) == 64


def test_portfolio_ranks_mminus_fixture_first() -> None:
    hypotheses = [cell.hypotheses[0] for cell in build_demo_cells()]
    scored = score_hypotheses(hypotheses)
    assert scored[0].statement.startswith("A linked negative-memory")
    assert pytest.approx(sum(item.normalized_priority for item in scored)) == 1.0


def test_budget_allocation_respects_total_and_max_share() -> None:
    scores = score_hypotheses([cell.hypotheses[0] for cell in build_demo_cells()])
    allocations = allocate_budget(scores, 100.0, minimum_test_budget=5.0, max_share=0.5)
    assert pytest.approx(sum(item.allocation for item in allocations), abs=1e-8) == 100.0
    assert max(item.allocation for item in allocations) <= 50.0 + 1e-8
    assert min(item.allocation for item in allocations) >= 5.0


def test_budget_allocation_rejects_impossible_minimums() -> None:
    scores = score_hypotheses([cell.hypotheses[0] for cell in build_demo_cells()])
    with pytest.raises(ValueError):
        allocate_budget(scores, 10.0, minimum_test_budget=5.0)


def _quality(**overrides: int) -> QualityObservation:
    values = dict(
        generated_objects=1000, unique_objects=950, formalized_claims=100,
        claims_with_evidence=80, claims_with_falsification=90,
        externally_validated_claims=10, duplicate_objects=20, orphan_objects=0,
        circular_evidence_links=0, repeated_errors_prevented=8,
        repeated_errors_observed=2,
    )
    values.update(overrides)
    return QualityObservation(**values)


def test_quality_conductor_expands_when_all_gates_pass() -> None:
    assert decide_quality(_quality()).decision is ConductorDecision.EXPAND


def test_quality_conductor_redesigns_reference_integrity_failure() -> None:
    assert decide_quality(_quality(orphan_objects=1)).decision is ConductorDecision.REDESIGN


def test_quality_conductor_reshards_excess_noise() -> None:
    observation = _quality(
        generated_objects=100, unique_objects=70, formalized_claims=20,
        claims_with_evidence=18, claims_with_falsification=18,
        externally_validated_claims=4, duplicate_objects=30,
    )
    assert decide_quality(observation).decision is ConductorDecision.RESHARD


def test_quality_conductor_holds_evidence_debt() -> None:
    assert decide_quality(_quality(claims_with_evidence=30)).decision is ConductorDecision.HOLD


def test_quality_conductor_holds_external_validation_bottleneck() -> None:
    assert decide_quality(_quality(externally_validated_claims=0)).decision is ConductorDecision.HOLD


def test_mminus_ablation_reduces_cost_and_repeated_failures() -> None:
    report = run_mminus_ablation(canonical_ablation_fixture())
    assert report.with_memory.total_cost < report.without_memory.total_cost
    assert report.with_memory.repeated_failures == 0
    assert report.without_memory.repeated_failures > 0
    assert report.cost_reduction > 0.4
    assert report.repeated_failure_reduction == 1.0
    assert report.rules


def test_mminus_ablation_measures_false_blocks() -> None:
    cases = (
        FailureCase.build("same", "domain", 2.0, True),
        FailureCase.build("same", "domain", 2.0, False),
    )
    report = run_mminus_ablation(cases)
    assert report.with_memory.false_blocks == 1
    assert report.net_prevention_gain == -1


def test_truth_audit_detects_known_divergence_classes() -> None:
    report = audit_repository(canonical_truth_audit_fixture())
    codes = {finding.code for finding in report.findings}
    assert {
        "VERSION_DIVERGENCE", "DOCUMENTED_SYMBOL_MISSING",
        "DOCUMENTED_TEST_CLAIM_UNSUPPORTED", "COMPLEXITY_DIVERGENCE",
        "DOCUMENTED_PATH_MISSING", "DEPENDENCY_VERSION_DIVERGENCE",
    } <= codes
    assert report.blocking is True


def test_truth_audit_clean_snapshot_has_no_blocking_findings() -> None:
    snapshot = RepositorySnapshot(
        repository="clean/repo", version="1.0", documented_version="1.0",
        public_symbols={"run"}, tested_symbols={"run"},
        documentation_claims=[
            DocumentationClaim("run exists", "symbol_exists", "run"),
            DocumentationClaim("run is tested", "tested", "run"),
        ],
    )
    report = audit_repository(snapshot)
    assert report.blocking is False
    assert report.finding_count == 0


def test_empirical_complexity_exponent_recovers_quadratic_growth() -> None:
    observations = [
        BenchmarkObservation("f", 100, 1), BenchmarkObservation("f", 200, 4),
        BenchmarkObservation("f", 400, 16), BenchmarkObservation("f", 800, 64),
    ]
    exponent = estimate_empirical_exponent(observations)
    assert exponent is not None
    assert exponent == pytest.approx(2.0, abs=1e-9)


def test_raman_loop_selects_full_candidate_and_beats_baseline() -> None:
    reference, training, holdout, peaks = canonical_raman_fixture()
    result = run_raman_loop(reference, training, holdout, peaks)
    assert result.best_candidate.kind is RamanModelKind.SHIFT_BROADENING_BASELINE
    assert result.best_candidate.holdout_rmse < result.baseline_rmse
    assert result.oak_transition == ("SIMULATED", "DEMONSTRATED")
    assert result.m_minus == ()


def test_raman_experiment_targets_largest_candidate_divergence() -> None:
    reference, training, holdout, peaks = canonical_raman_fixture()
    result = run_raman_loop(reference, training, holdout, peaks)
    assert result.experiment.condition in {1.5, 2.0, 2.5, 3.0, 4.0}
    assert result.experiment.expected_divergence > 0
    assert len(result.experiment.compared_candidates) == 2


def test_knowledge_cell_adapter_preserves_claim_identity() -> None:
    source = {
        "title": "Imported", "domain": "test", "description": "source description",
        "claims": [{"claim_id": "claim-1", "statement": "A works", "assumptions": ["scope"], "falsification_conditions": ["A fails"]}],
        "evidence": [{"kind": "test", "title": "test", "source": "tests/test.py", "supports": ["claim-1"]}],
    }
    cell = knowledge_cell_to_discovery_cell(source)
    assert cell.hypotheses[0].hypothesis_id == "claim-1"
    assert cell.evidence[0].supports == ("claim-1",)
    assert cell.validate() == []


def test_event_adapter_extracts_only_negative_events() -> None:
    records = [
        {"event_type": "ObservationEvent", "event_id": "e0", "payload": {}},
        {"event_type": "MMinusRule", "event_id": "e1", "payload": {
            "trigger": "failure", "root_cause": "cause",
            "forbidden_inference": "forbidden", "safe_replacement": "safe",
            "prevention_test": "test", "domain": "demo"}},
    ]
    rules = event_records_to_mminus(records)
    assert len(rules) == 1
    assert rules[0].source_event_ids == ("e1",)


def test_compiler_builds_manifest_and_all_three_proofs() -> None:
    compiler = RevolutionDiversificationCompiler(
        cells=build_demo_cells(), repository_snapshots=(canonical_truth_audit_fixture(),),
    )
    compiled = compiler.compile()
    assert compiled.metrics["module_count"] == 64
    assert compiled.metrics["cell_count"] == 3
    assert compiled.metrics["truth_audit_findings"] >= 6
    assert compiled.metrics["mminus_cost_reduction"] > 0
    assert compiled.metrics["raman_best_holdout_rmse"] < compiled.metrics["raman_baseline_rmse"]
    assert len(compiled.manifest["manifest_sha256"]) == 64


def test_compiler_export_writes_complete_bundle(tmp_path: Path) -> None:
    compiler = RevolutionDiversificationCompiler(
        cells=build_demo_cells(), repository_snapshots=(canonical_truth_audit_fixture(),),
    )
    compiled = compiler.export(tmp_path)
    expected = {"manifest.json", "metrics.json", "registry.json", "discovery-cells.json", "discovery-cells.jsonl", "truth-audits.json", "mminus-ablation.json", "raman-loop.json", "quality-observation.json", "quality-decision.json", "report.md"}
    assert expected <= {path.name for path in tmp_path.iterdir()}
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["manifest_sha256"] == compiled.manifest["manifest_sha256"]
    assert len((tmp_path / "discovery-cells.jsonl").read_text().splitlines()) == 3


def test_compiler_rejects_invalid_cells() -> None:
    cell = build_demo_cells()[0]
    cell.user = ""
    compiler = RevolutionDiversificationCompiler(cells=(cell,))
    with pytest.raises(ValueError, match="cell validation failed"):
        compiler.compile()


@pytest.mark.parametrize("command", ["registry", "mminus-ablation", "truth-audit", "raman-loop", "quality-demo"])
def test_cli_commands_return_json(command: str, tmp_path: Path) -> None:
    output = tmp_path / f"{command}.json"
    completed = subprocess.run(
        [sys.executable, "-m", "omega_revolution_diversification_t", command, "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    assert output.exists()
    assert json.loads(output.read_text())
    assert json.loads(completed.stdout)


def test_cli_compile_demo_exports_bundle(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    completed = subprocess.run(
        [sys.executable, "-m", "omega_revolution_diversification_t", "compile-demo", "--output-dir", str(output)],
        check=True, capture_output=True, text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["metrics"]["cell_count"] == 3
    assert (output / "report.md").exists()
