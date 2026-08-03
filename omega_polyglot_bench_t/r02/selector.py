"""Pareto and weighted multi-objective backend selection."""
from __future__ import annotations

from collections.abc import Iterable, Mapping

from .model import ScoreVector

COST_KEYS = ("latency_ns", "memory_bytes", "max_abs_error", "compile_ms")
BENEFIT_KEYS = ("throughput_per_s", "portability", "safety")


def dominates(left: ScoreVector, right: ScoreVector) -> bool:
    left.validate()
    right.validate()
    if not left.correct:
        return False
    if not right.correct:
        return True
    no_worse = all(getattr(left, key) <= getattr(right, key) for key in COST_KEYS)
    no_worse &= all(getattr(left, key) >= getattr(right, key) for key in BENEFIT_KEYS)
    strictly_better = any(getattr(left, key) < getattr(right, key) for key in COST_KEYS)
    strictly_better |= any(getattr(left, key) > getattr(right, key) for key in BENEFIT_KEYS)
    return no_worse and strictly_better


def pareto_front(scores: Iterable[ScoreVector]) -> tuple[ScoreVector, ...]:
    candidates = tuple(score for score in scores if score.correct)
    return tuple(
        score for score in candidates
        if not any(dominates(other, score) for other in candidates if other != score)
    )


def select_weighted(scores: Iterable[ScoreVector], weights: Mapping[str, float] | None = None) -> ScoreVector:
    candidates = tuple(score for score in scores if score.correct)
    if not candidates:
        raise ValueError("no correct variants")
    weights = dict(weights or {"latency": 0.35, "throughput": 0.25, "memory": 0.15, "error": 0.15, "safety": 0.10})
    maxima = {
        "latency": max(score.latency_ns for score in candidates) or 1,
        "throughput": max(score.throughput_per_s for score in candidates) or 1,
        "memory": max(score.memory_bytes for score in candidates) or 1,
        "error": max(score.max_abs_error for score in candidates) or 1,
    }

    def objective(score: ScoreVector) -> float:
        return (
            weights.get("latency", 0) * score.latency_ns / maxima["latency"]
            - weights.get("throughput", 0) * score.throughput_per_s / maxima["throughput"]
            + weights.get("memory", 0) * score.memory_bytes / maxima["memory"]
            + weights.get("error", 0) * score.max_abs_error / maxima["error"]
            - weights.get("safety", 0) * score.safety
        )

    return min(candidates, key=lambda score: (objective(score), score.variant_id))
