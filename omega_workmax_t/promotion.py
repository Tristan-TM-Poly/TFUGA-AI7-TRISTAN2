from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import ProofGates, WorkMetrics


@dataclass(frozen=True)
class PromotionDecision:
    status: str
    improvement_ratio: float
    reasons: tuple[str, ...]
    automatic_merge_authorized: bool = False

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


def _utility(metrics: WorkMetrics) -> float:
    return (
        metrics.validated_work_power
        * (0.5 + metrics.closure_ratio)
        * (1.0 + metrics.generative_leverage)
        / (1.0 + metrics.fanout_factor + metrics.queue_waste_ratio + metrics.duplicate_work_ratio)
    )


def decide_promotion(
    baseline: WorkMetrics,
    candidate: WorkMetrics,
    gates: ProofGates,
    *,
    minimum_improvement_ratio: float = 0.02,
) -> PromotionDecision:
    if minimum_improvement_ratio < 0:
        raise ValueError("minimum_improvement_ratio cannot be negative")
    if not gates.all_pass:
        failed = tuple(name for name, value in asdict(gates).items() if not value)
        return PromotionDecision("REJECT_PROOF_GATES", 0.0, failed)
    baseline_utility = _utility(baseline)
    candidate_utility = _utility(candidate)
    improvement = (candidate_utility - baseline_utility) / max(abs(baseline_utility), 1e-12)
    if candidate.fanout_factor > baseline.fanout_factor * 1.05:
        return PromotionDecision("REJECT_REGRESSION", improvement, ("fanout factor regressed materially",))
    if candidate.closure_ratio + 1e-12 < baseline.closure_ratio:
        return PromotionDecision("REJECT_REGRESSION", improvement, ("closure ratio regressed",))
    if improvement < minimum_improvement_ratio:
        return PromotionDecision("HOLD_NO_MATERIAL_GAIN", improvement, ("utility improvement below promotion threshold",))
    return PromotionDecision(
        "PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW",
        improvement,
        ("proof gates passed", "candidate improves safety-adjusted work utility"),
    )
