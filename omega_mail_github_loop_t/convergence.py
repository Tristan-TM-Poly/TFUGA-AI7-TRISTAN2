"""Convergence scoring and adaptive stopping rules."""
from __future__ import annotations

from dataclasses import dataclass

from .models import IterationMetrics, LoopCase, LoopDecision, LoopPolicy


@dataclass(frozen=True, slots=True)
class ConvergenceResult:
    decision: LoopDecision
    score: float
    reasons: tuple[str, ...]


def progress_score(metrics: IterationMetrics) -> float:
    return (
        0.80 * metrics.tests_added
        + 1.20 * metrics.tests_fixed
        + 2.00 * metrics.defects_removed
        + 2.50 * metrics.security_findings_removed
        + 0.75 * metrics.documentation_divergences_removed
        + 20.0 * metrics.coverage_delta
        - 6.0 * max(metrics.runtime_delta, 0.0)
        - 10.0 * max(metrics.false_positive_delta, 0.0)
        - 8.0 * max(metrics.risk_delta, 0.0)
        - 3.0 * max(metrics.complexity_delta, 0.0)
        - 0.05 * max(metrics.cost_units, 0.0)
    )


def evaluate_convergence(case: LoopCase, metrics: IterationMetrics, policy: LoopPolicy, *, acceptance_satisfied: bool = False, cumulative_cost: float = 0.0) -> ConvergenceResult:
    score = progress_score(metrics)
    if acceptance_satisfied:
        return ConvergenceResult(LoopDecision.STOP_ACCEPTED, score, ("acceptance_criteria_satisfied",))
    if cumulative_cost + metrics.cost_units > policy.adaptive_cost_budget:
        return ConvergenceResult(LoopDecision.STOP_BUDGET, score, ("adaptive_cost_budget_exhausted",))
    if case.repeated_failure_count >= policy.maximum_repeated_failure:
        return ConvergenceResult(LoopDecision.STOP_REPEATED_FAILURE, score, ("repeated_failure_threshold",))
    if score < policy.minimum_progress_score:
        if case.unchanged_reply_count + 1 >= policy.maximum_consecutive_no_gain:
            return ConvergenceResult(LoopDecision.STOP_NO_GAIN, score, ("consecutive_no_gain",))
        return ConvergenceResult(LoopDecision.CONTINUE, score, ("low_gain_checkpoint",))
    return ConvergenceResult(LoopDecision.CONTINUE, score, ("measurable_gain",))
