from __future__ import annotations

from dataclasses import dataclass, replace
import math
import random

from .models import Component, Material, RecoveryRoute
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class BetaFunctionalPosterior:
    """Beta posterior for a component's probability of being functional."""

    alpha: float = 1.0
    beta: float = 1.0

    def __post_init__(self) -> None:
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("alpha and beta must be positive")

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        total = self.alpha + self.beta
        return self.alpha * self.beta / (total * total * (total + 1.0))

    def updated(self, *, successes: float = 0.0, failures: float = 0.0) -> "BetaFunctionalPosterior":
        if successes < 0 or failures < 0:
            raise ValueError("successes and failures must be non-negative")
        return BetaFunctionalPosterior(self.alpha + successes, self.beta + failures)


@dataclass(frozen=True, slots=True)
class RoutePosteriorSummary:
    mode: str
    win_probability: float
    mean_score: float
    score_std: float


def bayesian_route_preferences(
    component: Component,
    materials: dict[str, Material],
    routes: tuple[RecoveryRoute, ...],
    posterior: BetaFunctionalPosterior,
    *,
    draws: int = 2_000,
    seed: int = 0,
    policy: ScoringPolicy | None = None,
) -> tuple[RoutePosteriorSummary, ...]:
    """Propagate functional-state uncertainty through route selection.

    Sampling is deterministic for a fixed seed. This is a model-level posterior,
    not empirical calibration or a safety certificate.
    """
    if draws <= 0:
        raise ValueError("draws must be positive")
    if not routes:
        raise ValueError("at least one route is required")
    if len({route.mode for route in routes}) != len(routes):
        raise ValueError("route modes must be unique for posterior summaries")

    policy = policy or ScoringPolicy()
    rng = random.Random(seed)
    wins = {route.mode.value: 0 for route in routes}
    score_sum = {route.mode.value: 0.0 for route in routes}
    score_sq_sum = {route.mode.value: 0.0 for route in routes}

    for _ in range(draws):
        probability = rng.betavariate(posterior.alpha, posterior.beta)
        probe = replace(component, functional_probability=probability)
        evaluations = [evaluate_route(probe, materials, route, policy) for route in routes]
        evaluations.sort(key=lambda evaluation: (-evaluation.score, evaluation.mode.value))
        wins[evaluations[0].mode.value] += 1
        for evaluation in evaluations:
            key = evaluation.mode.value
            score_sum[key] += evaluation.score
            score_sq_sum[key] += evaluation.score * evaluation.score

    summaries = []
    for route in routes:
        key = route.mode.value
        mean_score = score_sum[key] / draws
        variance = max(0.0, score_sq_sum[key] / draws - mean_score * mean_score)
        summaries.append(
            RoutePosteriorSummary(
                mode=key,
                win_probability=wins[key] / draws,
                mean_score=mean_score,
                score_std=math.sqrt(variance),
            )
        )
    summaries.sort(key=lambda item: (-item.win_probability, -item.mean_score, item.mode))
    return tuple(summaries)
