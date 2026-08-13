from __future__ import annotations

import json

from omega_meta_science_t.benchmark import build_fixture, report_as_dict, run_benchmark, run_strategy
from omega_meta_science_t.cli import main
from omega_meta_science_t.oak import FAULT_TYPES, inject_fault, evaluate_oak


def test_adaptive_disagreement_mining_selects_discriminating_experiment() -> None:
    problem = build_fixture()
    result = run_strategy(problem, "adaptive")
    assert result.selected_experiment.experiment_id == "E_discriminating"
    assert result.survivors == ("T_linear",)
    assert result.knowledge_gain_bits == 1.0
    assert result.verified_gain_per_cost == 1.0
    assert result.oak.decision == "PROMOTE"


def test_fixed_policy_remains_underdetermined_and_unpromoted() -> None:
    problem = build_fixture()
    result = run_strategy(problem, "fixed")
    assert result.selected_experiment.experiment_id == "E_fixed_alias"
    assert result.survivors == ("T_linear", "T_quadratic")
    assert result.knowledge_gain_bits == 0.0
    assert result.verified_gain_per_cost == 0.0
    assert result.oak.decision == "CONDITIONAL"
    assert "UNDERDETERMINED:2_SURVIVORS" in result.oak.warnings


def test_cvcd_preserves_cross_representation_invariants() -> None:
    result = run_strategy(build_fixture(), "adaptive")
    assert result.cvcd_invariants == ("domain:x>=0", "observable:y")


def test_meta_oak_detects_all_declared_epistemic_faults() -> None:
    report = run_benchmark()
    campaign = report.mutation_campaign
    assert campaign.injected == len(FAULT_TYPES)
    assert campaign.detected == len(FAULT_TYPES)
    assert campaign.mutation_score == 1.0
    assert campaign.missed_faults == ()
    for fault in FAULT_TYPES:
        mutated = inject_fault(report.adaptive.claim, fault)
        assert evaluate_oak(mutated).decision == "BLOCK"


def test_meta_evolution_promotes_adaptive_strategy_and_records_memory() -> None:
    report = run_benchmark()
    assert report.promoted_strategy == "adaptive"
    assert "strategy:adaptive" in report.m_plus
    assert "fixed_policy:underdetermined" in report.m_minus
    assert all(f"epistemic_fault:{fault}" in report.m_minus for fault in FAULT_TYPES)


def test_report_is_json_serializable() -> None:
    payload = report_as_dict(run_benchmark())
    text = json.dumps(payload, sort_keys=True)
    assert '"promoted_strategy": "adaptive"' in text


def test_cli_emits_json(capsys) -> None:
    assert main(["--compact"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["promoted_strategy"] == "adaptive"
    assert payload["mutation_campaign"]["mutation_score"] == 1.0
