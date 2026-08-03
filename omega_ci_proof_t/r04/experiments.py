from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from .models import (
    CausalDiagnosis,
    DiscriminationPlan,
    ExperimentDesign,
    ExperimentRecommendation,
    FORBIDDEN_CAPABILITIES,
    shannon_entropy,
)


def experiments_from_mapping(raw: Mapping[str, Any]) -> tuple[ExperimentDesign, ...]:
    return tuple(
        ExperimentDesign(
            experiment_id=str(item["experiment_id"]),
            description=str(item["description"]),
            outcomes=tuple(str(value) for value in item["outcomes"]),
            likelihoods={
                str(hypothesis_id): {str(outcome): float(value) for outcome, value in distribution.items()}
                for hypothesis_id, distribution in item["likelihoods"].items()
            },
            compute_cost=float(item.get("compute_cost", 0.0)),
            human_cost=float(item.get("human_cost", 0.0)),
            safety_risk=float(item.get("safety_risk", 0.0)),
            required_capability=str(item.get("required_capability", "run_tests")),
            affected_claim_ids=tuple(str(value) for value in item.get("affected_claim_ids", ())),
        )
        for item in raw.get("experiments", ())
    )


class DiscriminatingExperimentPlanner:
    def __init__(self, *, max_safety_risk: float = 0.30) -> None:
        if not 0.0 <= max_safety_risk <= 1.0:
            raise ValueError("max_safety_risk must be in [0, 1]")
        self.max_safety_risk = max_safety_risk

    def _support(self, diagnosis: CausalDiagnosis) -> dict[str, float]:
        return {item.hypothesis_id: item.support_score for item in diagnosis.assessments}

    def _score(self, design: ExperimentDesign, support: Mapping[str, float]) -> ExperimentRecommendation:
        unknown = sorted(set(design.likelihoods).difference(support))
        missing = sorted(set(support).difference(design.likelihoods))
        if unknown or missing:
            raise KeyError(f"experiment hypothesis mismatch; unknown={unknown}, missing={missing}")

        prior_entropy = shannon_entropy(tuple(support.values()))
        outcome_probabilities: dict[str, float] = defaultdict(float)
        for hypothesis_id, hypothesis_support in support.items():
            for outcome, likelihood in design.likelihoods[hypothesis_id].items():
                outcome_probabilities[outcome] += hypothesis_support * likelihood

        expected_posterior_entropy = 0.0
        for outcome, outcome_probability in outcome_probabilities.items():
            if outcome_probability <= 0:
                continue
            posterior = []
            for hypothesis_id, hypothesis_support in support.items():
                posterior.append(hypothesis_support * design.likelihoods[hypothesis_id][outcome] / outcome_probability)
            expected_posterior_entropy += outcome_probability * shannon_entropy(tuple(posterior))
        information_gain = max(0.0, prior_entropy - expected_posterior_entropy)
        cost = max(0.001, design.total_cost)
        utility = information_gain * max(0.0, 1.0 - design.safety_risk) / cost
        return ExperimentRecommendation(
            experiment_id=design.experiment_id,
            expected_information_gain=round(information_gain, 12),
            utility=round(utility, 12),
            cost=round(design.total_cost, 12),
            safety_risk=design.safety_risk,
            expected_outcome_distribution={key: round(value, 12) for key, value in outcome_probabilities.items()},
            reason="maximizes expected hypothesis discrimination per bounded cost under the declared model",
        )

    def plan(
        self,
        diagnosis: CausalDiagnosis,
        designs: Sequence[ExperimentDesign],
        *,
        budget: float,
    ) -> DiscriminationPlan:
        if budget < 0:
            raise ValueError("budget cannot be negative")
        support = self._support(diagnosis)
        recommendations = []
        rejected: dict[str, str] = {}
        design_by_id = {item.experiment_id: item for item in designs}
        if len(design_by_id) != len(designs):
            raise ValueError("duplicate experiment IDs")

        for design in designs:
            if design.required_capability in FORBIDDEN_CAPABILITIES:
                rejected[design.experiment_id] = "sensitive capability is forbidden at A3"
                continue
            if design.safety_risk > self.max_safety_risk:
                rejected[design.experiment_id] = "safety risk exceeds the A3 planning threshold"
                continue
            recommendation = self._score(design, support)
            if recommendation.expected_information_gain <= 1e-12:
                rejected[design.experiment_id] = "experiment does not discriminate modeled hypotheses"
                continue
            recommendations.append(recommendation)

        recommendations.sort(key=lambda item: (-item.utility, item.experiment_id))
        selected = []
        consumed = 0.0
        information_gain = 0.0
        for recommendation in recommendations:
            if consumed + recommendation.cost <= budget + 1e-12:
                selected.append(recommendation)
                consumed += recommendation.cost
                information_gain += recommendation.expected_information_gain
            else:
                rejected[recommendation.experiment_id] = "insufficient declared budget"
        return DiscriminationPlan(
            failure_id=diagnosis.failure_id,
            recommendations=tuple(selected),
            rejected=rejected,
            budget=budget,
            consumed_budget=consumed,
            expected_information_gain=information_gain,
        )
