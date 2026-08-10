from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Component, Material, RecoveryPlan, RecoveryRoute
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class Candidate:
    component: Component
    routes: tuple[RecoveryRoute, ...]


class RecoveryOptimizer:
    """Deterministic component-wise recovery trajectory optimizer.

    R0.1 deliberately solves independent component decisions. Coupled plant,
    transport, capacity and inventory constraints are reserved for later releases.
    """

    def __init__(self, materials: dict[str, Material], policy: ScoringPolicy | None = None) -> None:
        self.materials = materials
        self.policy = policy or ScoringPolicy()

    def optimize(self, candidates: Iterable[Candidate]) -> RecoveryPlan:
        plan = RecoveryPlan()
        for candidate in sorted(candidates, key=lambda c: c.component.component_id):
            if not candidate.routes:
                raise ValueError(f"no routes for component {candidate.component.component_id}")
            evaluations = [evaluate_route(candidate.component, self.materials, route, self.policy) for route in candidate.routes]
            evaluations.sort(key=lambda e: (-e.score, e.mode.value))
            plan.evaluations.append(evaluations[0])
        return plan
