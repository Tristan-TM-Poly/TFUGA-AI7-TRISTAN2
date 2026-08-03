from __future__ import annotations

from .bisect import BisectPlanner
from .causal import CausalDiagnosticEngine
from .counterfactual import CounterfactualProjector
from .dossier import CausalDossierBuilder
from .experiments import DiscriminatingExperimentPlanner, experiments_from_mapping
from .minimize import DeltaMinimizer


def _fixture_model():
    return {
        "failure_id": "FAIL-DOT-GITHUB",
        "hypotheses": [
            {
                "hypothesis_id": "H-LSTRIP",
                "statement": "broad lstrip removes the leading dot",
                "cause_node_ids": ["NORMALIZER"],
                "prior_weight": 1.0,
                "assumptions": ["fixture reaches normalize_path"],
                "falsifiers": ["exact-prefix implementation still loses the dot"],
            },
            {
                "hypothesis_id": "H-FIXTURE",
                "statement": "fixture serialization removes the dot",
                "cause_node_ids": ["FIXTURE"],
                "prior_weight": 1.0,
                "falsifiers": ["raw fixture bytes preserve the dot"],
            },
            {
                "hypothesis_id": "H-OS",
                "statement": "platform path semantics remove the dot",
                "cause_node_ids": ["ENVIRONMENT"],
                "prior_weight": 1.0,
                "falsifiers": ["same behavior occurs on all platforms"],
            },
        ],
    }


def _fixture_observations():
    return {
        "observations": [
            {
                "observation_id": "OBS-MINIMAL",
                "statement": "minimal direct call loses the leading dot",
                "likelihood_by_hypothesis": {"H-LSTRIP": 0.98, "H-FIXTURE": 0.20, "H-OS": 0.25},
                "reliability": 0.95,
            },
            {
                "observation_id": "OBS-RAW-FIXTURE",
                "statement": "raw fixture bytes preserve the leading dot",
                "likelihood_by_hypothesis": {"H-LSTRIP": 0.90, "H-FIXTURE": 0.05, "H-OS": 0.40},
                "reliability": 0.90,
            },
            {
                "observation_id": "OBS-CROSS-PLATFORM",
                "statement": "failure reproduces on two platforms",
                "likelihood_by_hypothesis": {"H-LSTRIP": 0.85, "H-FIXTURE": 0.35, "H-OS": 0.10},
                "reliability": 0.85,
            },
        ],
    }


def _fixture_experiments():
    return {
        "experiments": [
            {
                "experiment_id": "EXP-EXACT-PREFIX",
                "description": "compare exact-prefix removal with broad lstrip in an isolated fixture",
                "outcomes": ["exact_passes", "both_fail"],
                "likelihoods": {
                    "H-LSTRIP": {"exact_passes": 0.95, "both_fail": 0.05},
                    "H-FIXTURE": {"exact_passes": 0.20, "both_fail": 0.80},
                    "H-OS": {"exact_passes": 0.35, "both_fail": 0.65},
                },
                "compute_cost": 0.10,
                "human_cost": 0.05,
                "safety_risk": 0.0,
            },
            {
                "experiment_id": "EXP-PUBLISH",
                "description": "publish preliminary result",
                "outcomes": ["published", "blocked"],
                "likelihoods": {
                    "H-LSTRIP": {"published": 0.5, "blocked": 0.5},
                    "H-FIXTURE": {"published": 0.5, "blocked": 0.5},
                    "H-OS": {"published": 0.5, "blocked": 0.5},
                },
                "compute_cost": 0.01,
                "human_cost": 0.01,
                "safety_risk": 0.0,
                "required_capability": "publish",
            },
        ],
    }


def run_oakbench() -> dict[str, object]:
    model = _fixture_model()
    engine = CausalDiagnosticEngine.from_mapping(model)
    observations = engine.observations_from_mapping(_fixture_observations())
    diagnosis = engine.diagnose(model["failure_id"], observations)
    experiments = experiments_from_mapping(_fixture_experiments())
    plan = DiscriminatingExperimentPlanner().plan(diagnosis, experiments, budget=0.5)
    reproduction = DeltaMinimizer().minimize_required_tokens_fixture(
        model["failure_id"],
        ("prefix", "noise-a", ".github", "noise-b", "workflow"),
        (".github", "workflow"),
    )
    bisect_plan = BisectPlanner().plan(
        model["failure_id"],
        ("c0", "c1", "c2", "c3", "c4"),
        "c0",
        "c4",
    )
    selected_design = next(item for item in experiments if item.experiment_id == plan.recommendations[0].experiment_id)
    worlds = CounterfactualProjector().project(engine.hypotheses, selected_design)
    dossier = CausalDossierBuilder().build(diagnosis, plan, reproduction, bisect_plan, worlds)
    checks = {
        "leading_hypothesis_is_lstrip": diagnosis.top_hypothesis_id == "H-LSTRIP",
        "diagnosis_is_heuristic_not_proof": diagnosis.to_dict()["causality_proven"] is False,
        "information_gain_positive": diagnosis.information_gain > 0,
        "safe_experiment_selected": [item.experiment_id for item in plan.recommendations] == ["EXP-EXACT-PREFIX"],
        "publish_rejected": "EXP-PUBLISH" in plan.rejected,
        "minimal_reproduction_preserved": reproduction.preserved_failure and set(reproduction.minimized_items) == {".github", "workflow"},
        "bisect_is_plan_only": bisect_plan.to_dict()["execution_authorized"] is False,
        "dossier_a3_only": dossier.to_dict()["maximum_authority"] == "A3",
        "no_remote_mutations": dossier.to_dict()["remote_mutations"] == 0,
        "automatic_patch_disabled": dossier.to_dict()["automatic_patch_allowed"] is False,
    }
    return {
        "schema": "omega-ci-r04-oakbench/v4",
        "passed": all(checks.values()),
        "checks": checks,
        "diagnosis_id": diagnosis.diagnosis_id,
        "dossier_id": dossier.dossier_id,
        "maximum_authority": "A3",
        "causality_proven": False,
        "automatic_patch_allowed": False,
        "automatic_merge_allowed": False,
        "remote_mutations": 0,
    }
