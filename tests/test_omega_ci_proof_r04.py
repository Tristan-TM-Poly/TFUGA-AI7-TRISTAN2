from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_ci_proof_t.r04.bisect import BisectPlanner
from omega_ci_proof_t.r04.causal import CausalDiagnosticEngine
from omega_ci_proof_t.r04.counterfactual import CounterfactualProjector
from omega_ci_proof_t.r04.dossier import CausalDossierBuilder
from omega_ci_proof_t.r04.experiments import DiscriminatingExperimentPlanner, experiments_from_mapping
from omega_ci_proof_t.r04.minimize import DeltaMinimizer
from omega_ci_proof_t.r04.models import CausalHypothesis, CausalObservation, ExperimentDesign
from omega_ci_proof_t.r04.oak import run_oakbench

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "omega_ci_proof_t"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def engine() -> CausalDiagnosticEngine:
    return CausalDiagnosticEngine.from_mapping(load("r04-model.json"))


def diagnosis():
    eng = engine()
    return eng.diagnose("FAIL-DOT-GITHUB", eng.observations_from_mapping(load("r04-observations.json")))


def designs():
    return experiments_from_mapping(load("r04-experiments.json"))


def test_hypothesis_requires_positive_prior():
    with pytest.raises(ValueError):
        CausalHypothesis("H", "x", (), 0)


def test_observation_rejects_invalid_reliability():
    with pytest.raises(ValueError):
        CausalObservation("O", "x", {"H": 0.5}, reliability=1.1)


def test_observation_rejects_invalid_likelihood():
    with pytest.raises(ValueError):
        CausalObservation("O", "x", {"H": 1.1})


def test_engine_rejects_duplicate_hypotheses():
    hypothesis = CausalHypothesis("H", "x", (), 1)
    with pytest.raises(ValueError, match="duplicate"):
        CausalDiagnosticEngine((hypothesis, hypothesis))


def test_observation_requires_every_modeled_hypothesis():
    eng = engine()
    raw = load("r04-observations.json")
    del raw["observations"][0]["likelihood_by_hypothesis"]["H-OS"]
    with pytest.raises(KeyError, match="omits"):
        eng.observations_from_mapping(raw)


def test_diagnosis_is_deterministic_under_reversed_hypotheses_and_observations():
    model = load("r04-model.json")
    observations = load("r04-observations.json")
    a_engine = CausalDiagnosticEngine.from_mapping(model)
    a = a_engine.diagnose(model["failure_id"], a_engine.observations_from_mapping(observations)).diagnosis_id
    model["hypotheses"] = list(reversed(model["hypotheses"]))
    observations["observations"] = list(reversed(observations["observations"]))
    b_engine = CausalDiagnosticEngine.from_mapping(model)
    b = b_engine.diagnose(model["failure_id"], b_engine.observations_from_mapping(observations)).diagnosis_id
    assert a == b


def test_diagnosis_ranks_lstrip_first():
    report = diagnosis()
    assert report.top_hypothesis_id == "H-LSTRIP"
    assert report.assessments[0].rank == 1


def test_diagnosis_is_heuristically_supported():
    assert diagnosis().status == "HEURISTICALLY_SUPPORTED"


def test_diagnosis_information_gain_is_positive():
    report = diagnosis()
    assert report.information_gain > 0
    assert report.posterior_entropy < report.prior_entropy


def test_diagnosis_explicitly_does_not_prove_causality():
    payload = diagnosis().to_dict()
    assert payload["causality_proven"] is False
    assert payload["automatic_patch_allowed"] is False
    assert payload["remote_mutations"] == 0


def test_empty_observations_are_insufficient():
    report = engine().diagnose("F", ())
    assert report.status == "INSUFFICIENT_EVIDENCE"


def test_balanced_observations_remain_ambiguous():
    eng = engine()
    likelihoods = {key: 0.5 for key in eng.by_id}
    observation = CausalObservation("O", "balanced", likelihoods)
    report = eng.diagnose("F", (observation,))
    assert report.status == "AMBIGUOUS"


def test_assessment_records_evidence_for_and_against():
    report = diagnosis()
    leading = report.assessments[0]
    assert "OBS-DIRECT-CALL" in leading.evidence_for
    os_assessment = next(item for item in report.assessments if item.hypothesis_id == "H-OS")
    assert "OBS-CROSS-PLATFORM" in os_assessment.evidence_against


def test_experiment_rejects_bad_distribution():
    with pytest.raises(ValueError, match="sum"):
        ExperimentDesign("E", "x", ("a", "b"), {"H": {"a": 0.8, "b": 0.8}}, 1, 1, 0)


def test_experiment_plan_selects_safe_discriminating_designs():
    plan = DiscriminatingExperimentPlanner().plan(diagnosis(), designs(), budget=1.0)
    ids = [item.experiment_id for item in plan.recommendations]
    assert "EXP-NORMALIZER-AB" in ids
    assert "EXP-DIRECT-VS-CALLER" in ids
    assert plan.consumed_budget <= 1.0


def test_experiment_plan_rejects_publish():
    plan = DiscriminatingExperimentPlanner().plan(diagnosis(), designs(), budget=10.0)
    assert plan.rejected["EXP-PUBLISH-PRELIMINARY"] == "sensitive capability is forbidden at A3"


def test_experiment_plan_rejects_high_risk_remote_mutation():
    plan = DiscriminatingExperimentPlanner().plan(diagnosis(), designs(), budget=10.0)
    assert "EXP-HIGH-RISK-REMOTE-MUTATION" in plan.rejected


def test_experiment_plan_never_authorizes_execution():
    payload = DiscriminatingExperimentPlanner().plan(diagnosis(), designs(), budget=1.0).to_dict()
    assert payload["execution_authorized"] is False
    assert payload["automatic_patch_allowed"] is False
    assert payload["remote_mutations"] == 0


def test_experiment_plan_rejects_negative_budget():
    with pytest.raises(ValueError):
        DiscriminatingExperimentPlanner().plan(diagnosis(), designs(), budget=-1)


def test_experiment_mismatch_is_rejected():
    bad = list(designs())
    raw = bad[0].to_dict()
    raw["likelihoods"].pop("H-CALLER")
    malformed = ExperimentDesign(
        raw["experiment_id"], raw["description"], tuple(raw["outcomes"]), raw["likelihoods"],
        raw["compute_cost"], raw["human_cost"], raw["safety_risk"], raw["required_capability"],
        tuple(raw["affected_claim_ids"]),
    )
    with pytest.raises(KeyError, match="mismatch"):
        DiscriminatingExperimentPlanner().plan(diagnosis(), (malformed,), budget=1)


def test_minimizer_preserves_failure_and_reduces_fixture():
    raw = load("r04-case.json")
    receipt = DeltaMinimizer().minimize_required_tokens_fixture(raw["failure_id"], raw["items"], raw["required_tokens"])
    assert receipt.preserved_failure
    assert set(receipt.minimized_items) == set(raw["required_tokens"])
    assert receipt.reduction_ratio > 0


def test_minimizer_rejects_non_reproducing_original():
    with pytest.raises(ValueError, match="does not reproduce"):
        DeltaMinimizer().minimize("F", ("a", "b"), lambda _: False)


def test_minimizer_honors_evaluation_limit():
    receipt = DeltaMinimizer().minimize("F", tuple(str(i) for i in range(20)), lambda candidate: "0" in candidate, max_evaluations=2)
    assert receipt.limit_reached


def test_minimizer_is_deterministic():
    raw = load("r04-case.json")
    a = DeltaMinimizer().minimize_required_tokens_fixture(raw["failure_id"], raw["items"], raw["required_tokens"]).reproduction_id
    b = DeltaMinimizer().minimize_required_tokens_fixture(raw["failure_id"], raw["items"], raw["required_tokens"]).reproduction_id
    assert a == b


def test_bisect_plans_midpoint_without_execution():
    raw = load("r04-history.json")
    plan = BisectPlanner().plan(raw["failure_id"], raw["ordered_commits"], raw["known_good_sha"], raw["known_bad_sha"], tested_verdicts=raw["tested_verdicts"])
    assert plan.next_step is not None
    assert plan.next_step.candidate_sha == "c002"
    assert plan.to_dict()["execution_authorized"] is False


def test_bisect_updates_boundary_with_verdicts():
    commits = ("c0", "c1", "c2", "c3", "c4")
    plan = BisectPlanner().plan("F", commits, "c0", "c4", tested_verdicts={"c2": "GOOD", "c3": "BAD"})
    assert plan.status == "BOUNDARY_IDENTIFIED"
    assert plan.known_good_sha == "c2"
    assert plan.known_bad_sha == "c3"


def test_bisect_rejects_reversed_boundary():
    with pytest.raises(ValueError):
        BisectPlanner().plan("F", ("c0", "c1"), "c1", "c0")


def test_bisect_rejects_unknown_verdict_commit():
    with pytest.raises(KeyError):
        BisectPlanner().plan("F", ("c0", "c1", "c2"), "c0", "c2", tested_verdicts={"x": "GOOD"})


def test_counterfactual_worlds_cover_every_hypothesis():
    eng = engine()
    design = next(item for item in designs() if item.experiment_id == "EXP-NORMALIZER-AB")
    worlds = CounterfactualProjector().project(eng.hypotheses, design)
    assert {item.hypothesis_id for item in worlds} == set(eng.by_id)


def test_counterfactual_rejects_incomplete_experiment():
    eng = engine()
    raw = next(item for item in designs() if item.experiment_id == "EXP-NORMALIZER-AB").to_dict()
    raw["likelihoods"].pop("H-OS")
    design = ExperimentDesign(
        raw["experiment_id"], raw["description"], tuple(raw["outcomes"]), raw["likelihoods"],
        raw["compute_cost"], raw["human_cost"], raw["safety_risk"], raw["required_capability"],
        tuple(raw["affected_claim_ids"]),
    )
    with pytest.raises(KeyError):
        CounterfactualProjector().project(eng.hypotheses, design)


def test_dossier_preserves_a3_and_human_review():
    eng = engine()
    report = diagnosis()
    exp = designs()
    plan = DiscriminatingExperimentPlanner().plan(report, exp, budget=1.0)
    raw_case = load("r04-case.json")
    reproduction = DeltaMinimizer().minimize_required_tokens_fixture(raw_case["failure_id"], raw_case["items"], raw_case["required_tokens"])
    raw_history = load("r04-history.json")
    bisect_plan = BisectPlanner().plan(raw_history["failure_id"], raw_history["ordered_commits"], raw_history["known_good_sha"], raw_history["known_bad_sha"], tested_verdicts=raw_history["tested_verdicts"])
    selected = next(item for item in exp if item.experiment_id == plan.recommendations[0].experiment_id)
    worlds = CounterfactualProjector().project(eng.hypotheses, selected)
    payload = CausalDossierBuilder().build(report, plan, reproduction, bisect_plan, worlds).to_dict()
    assert payload["maximum_authority"] == "A3"
    assert payload["causality_proven"] is False
    assert payload["automatic_patch_allowed"] is False
    assert payload["automatic_merge_allowed"] is False
    assert payload["human_review_required"] is True
    assert payload["remote_mutations"] == 0


def test_dossier_rejects_mixed_failures():
    eng = engine()
    report = diagnosis()
    plan = DiscriminatingExperimentPlanner().plan(report, designs(), budget=1.0)
    reproduction = DeltaMinimizer().minimize_required_tokens_fixture("OTHER", ("x",), ("x",))
    bisect_plan = BisectPlanner().plan("FAIL-DOT-GITHUB", ("c0", "c1"), "c0", "c1")
    with pytest.raises(ValueError, match="same failure"):
        CausalDossierBuilder().build(report, plan, reproduction, bisect_plan, ())


def test_oakbench_passes_and_preserves_a3():
    result = run_oakbench()
    assert result["passed"]
    assert result["maximum_authority"] == "A3"
    assert result["causality_proven"] is False
    assert result["automatic_patch_allowed"] is False
    assert result["automatic_merge_allowed"] is False
    assert result["remote_mutations"] == 0
