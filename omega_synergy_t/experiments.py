"""Causal experiment compiler and counterfactual twin plans."""
from __future__ import annotations

from .models import ExperimentPlan, SynergyCandidate, stable_id


def compile_experiment(candidate: SynergyCandidate) -> ExperimentPlan:
    systems = " × ".join(candidate.systems)
    interfaces = [contract.id for contract in candidate.proposed_interfaces]
    return ExperimentPlan(
        id=stable_id("EXP", candidate.id, candidate.systems),
        candidate_id=candidate.id,
        hypothesis=f"{systems} closes documented needs and yields a measurable gain caused by the composition rather than by uncontrolled configuration changes.",
        baselines=[
            f"Run each component in isolation: {', '.join(candidate.systems)}",
            candidate.simplest_baseline,
            "Use a no-adapter placebo path with identical inputs and measurement code.",
        ],
        ablations=[
            "Remove each proposed interface one at a time.",
            "Disable capability-to-need routing while preserving all other code.",
            "Replace inferred mappings with identity or null mappings.",
        ],
        controls=[
            "Negative-control task where no synergy is expected.",
            "Frozen dataset and deterministic seed.",
            "Independent metric collector not used by the optimizer.",
        ],
        perturbations=[
            "Input noise and missing metadata.",
            "Dependency/version changes.",
            "Adversarially similar but semantically incompatible artifacts.",
        ],
        metrics=[
            "task_quality", "latency", "compute_cost", "error_rate", "provenance_integrity",
            "closure_rate", "proof_density", "integration_debt", "human_review_time",
        ],
        success_criteria=[
            "Composition beats the strongest isolated baseline on a preregistered primary metric.",
            "No critical provenance, safety, license, or rollback regression.",
            "At least one ablation removes a material fraction of the measured gain.",
        ],
        failure_criteria=[
            "A simpler baseline performs equivalently within uncertainty.",
            "The gain vanishes under deterministic rerun or minor perturbation.",
            "The composition creates unacceptable debt or irreversible risk.",
        ],
        stopping_rules=[
            "Stop on any policy-gate violation.",
            "Stop after the preregistered compute budget is exhausted.",
            "Archive to M⁻ after repeated non-improvement against the simplest baseline.",
        ],
        oak_gates=[
            "provenance_required", "baseline_required", "ablation_required",
            "uncertainty_required", "license_gate", "rollback_verified",
            "no_claim_promotion_without_independent_evidence",
        ],
        rollback=[
            "Revert the experiment branch or draft PR.",
            "Restore the last verified interface contract and evidence ledger checkpoint.",
            "Preserve failure artifacts in M⁻ without promoting claims.",
        ],
        expected_artifacts=[
            "hypothesis.md", "experiment.json", "baseline-results.json", "ablation-results.json",
            "oak-report.json", "uncertainty.json", "rollback.md", "evidence-manifest.json",
            *[f"interface/{item}.json" for item in interfaces],
        ],
    )


def counterfactual_twin(candidate: SynergyCandidate) -> dict:
    return {
        "candidate_id": candidate.id,
        "observed_world": {"composition": candidate.systems, "interfaces": [item.id for item in candidate.proposed_interfaces]},
        "counterfactual_worlds": [
            {"name": "component_isolation", "remove": [system], "preserve": [item for item in candidate.systems if item != system]}
            for system in candidate.systems
        ] + [
            {"name": "simplest_external_baseline", "replace_all": candidate.simplest_baseline},
            {"name": "adapter_placebo", "replace_interfaces_with": "identity_or_null_adapter"},
        ],
        "questions": [
            "Which component causes the marginal gain?",
            "Could a simpler design obtain the same result?",
            "Does the gain persist under perturbation and independent measurement?",
        ],
        "authority": "review_only_heuristic",
    }
