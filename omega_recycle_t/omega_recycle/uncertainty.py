from __future__ import annotations

from dataclasses import dataclass, replace

from .models import Component, Material, RecoveryRoute
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class RouteSwitch:
    probability: float
    winning_mode: str
    score: float


def functional_probability_sweep(component: Component, materials: dict[str, Material], routes: tuple[RecoveryRoute, ...], *, steps: int = 21, policy: ScoringPolicy | None = None) -> tuple[RouteSwitch, ...]:
    """Deterministic sensitivity sweep over component functional probability."""
    if steps < 2:
        raise ValueError("steps must be >= 2")
    policy = policy or ScoringPolicy()
    result: list[RouteSwitch] = []
    for index in range(steps):
        probability = index / (steps - 1)
        probe = replace(component, functional_probability=probability)
        evaluations = [evaluate_route(probe, materials, route, policy) for route in routes]
        evaluations.sort(key=lambda e: (-e.score, e.mode.value))
        winner = evaluations[0]
        result.append(RouteSwitch(probability=round(probability, 12), winning_mode=winner.mode.value, score=winner.score))
    return tuple(result)


def switching_thresholds(sweep: tuple[RouteSwitch, ...]) -> tuple[RouteSwitch, ...]:
    """Return the first sampled point of each new winning regime."""
    if not sweep:
        return ()
    thresholds = [sweep[0]]
    previous = sweep[0].winning_mode
    for point in sweep[1:]:
        if point.winning_mode != previous:
            thresholds.append(point)
            previous = point.winning_mode
    return tuple(thresholds)
