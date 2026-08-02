from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

from .self_improvement import (
    PromotionDecision,
    SelfImprovementLab as RawSelfImprovementLab,
    SelfImprovementReport,
    VariantOutcome,
)


class ResourceAwareSelfImprovementLab(RawSelfImprovementLab):
    """OAK judge that penalizes capacity overshoot and reward hacking.

    A policy cannot win only by allocating a much larger temporary frontier.
    The score includes the ratio between final allocated capacity and the
    largest batch that was actually demonstrated as safe.
    """

    def __init__(
        self,
        output_dir: str | Path,
        *,
        overshoot_penalty_weight: float = 10.0,
        maximum_overshoot_multiplier: float = 3.0,
        **kwargs: Any,
    ):
        if overshoot_penalty_weight < 0.0:
            raise ValueError("overshoot_penalty_weight cannot be negative")
        if maximum_overshoot_multiplier < 1.0:
            raise ValueError("maximum_overshoot_multiplier must be at least 1")
        super().__init__(output_dir, **kwargs)
        self.overshoot_penalty_weight = overshoot_penalty_weight
        self.maximum_overshoot_multiplier = maximum_overshoot_multiplier

    @staticmethod
    def capacity_overshoot_ratio(outcome: VariantOutcome) -> float:
        return sum(
            max(0.0, scenario.final_capacity / max(1, scenario.largest_safe_batch) - 1.0)
            for scenario in outcome.scenarios
        )

    def _evaluate(
        self,
        variant,
        *,
        run_id: str,
        role: str,
    ) -> VariantOutcome:
        outcome = super()._evaluate(variant, run_id=run_id, role=role)
        overshoot = self.capacity_overshoot_ratio(outcome)
        denominator = max(
            1.0,
            outcome.total_iterations
            + 8 * outcome.total_saturations
            + 4 * outcome.total_redesigns
            + self.overshoot_penalty_weight * overshoot,
        )
        return replace(
            outcome,
            efficiency_score=outcome.total_integrated / denominator,
        )

    def _regressions(
        self,
        baseline: VariantOutcome,
        candidate: VariantOutcome,
    ) -> tuple[str, ...]:
        reasons = list(super()._regressions(baseline, candidate))
        baseline_overshoot = self.capacity_overshoot_ratio(baseline)
        candidate_overshoot = self.capacity_overshoot_ratio(candidate)
        allowed = max(
            baseline_overshoot * self.maximum_overshoot_multiplier,
            baseline_overshoot + 0.25,
        )
        if candidate_overshoot > allowed:
            reasons.append("capacity overshoot exceeded the permitted multiplier")
        return tuple(reasons)

    def _promotion_plan(self, report: SelfImprovementReport) -> dict[str, Any]:
        plan = super()._promotion_plan(report)
        selected = next(
            (
                item
                for item in report.candidates
                if item.variant.fingerprint == report.decision.selected_fingerprint
            ),
            None,
        )
        plan["evidence"]["judge"] = {
            "type": "resource_aware_oak_judge",
            "overshoot_penalty_weight": self.overshoot_penalty_weight,
            "maximum_overshoot_multiplier": self.maximum_overshoot_multiplier,
            "baseline_capacity_overshoot_ratio": self.capacity_overshoot_ratio(report.baseline),
            "selected_capacity_overshoot_ratio": (
                self.capacity_overshoot_ratio(selected) if selected is not None else None
            ),
        }
        return plan

    def _decide(
        self,
        baseline: VariantOutcome,
        candidates: Sequence[VariantOutcome],
    ) -> PromotionDecision:
        decision = super()._decide(baseline, candidates)
        if decision.status != "promotion_proposed":
            return decision
        return replace(
            decision,
            reasons=decision.reasons
            + (
                "capacity overshoot stayed inside the OAK multiplier",
                "capacity overshoot was penalized in the efficiency score",
            ),
        )
