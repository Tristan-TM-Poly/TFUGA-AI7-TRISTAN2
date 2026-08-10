from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

from .models import Material, RecoveryPlan, RouteEvaluation
from .optimizer import Candidate
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class FlowConstraints:
    max_process_cost: float | None = None
    max_energy_kwh: float | None = None
    max_risk_sum: float | None = None

    def __post_init__(self) -> None:
        for value in (self.max_process_cost, self.max_energy_kwh, self.max_risk_sum):
            if value is not None and value < 0:
                raise ValueError("flow limits must be non-negative")


@dataclass(frozen=True, slots=True)
class GlobalOptimizationResult:
    plan: RecoveryPlan
    feasible_combinations: int
    evaluated_combinations: int


class ConstrainedRecoveryOptimizer:
    """Exact deterministic optimizer for small coupled recovery problems.

    R0.2 uses exhaustive enumeration as a transparent benchmark oracle. It is
    intentionally not presented as a scalable industrial solver.
    """

    def __init__(self, materials: dict[str, Material], policy: ScoringPolicy | None = None) -> None:
        self.materials = materials
        self.policy = policy or ScoringPolicy()

    def optimize(self, candidates: Iterable[Candidate], constraints: FlowConstraints) -> GlobalOptimizationResult:
        ordered = tuple(sorted(candidates, key=lambda c: c.component.component_id))
        if any(not candidate.routes for candidate in ordered):
            raise ValueError("every candidate must expose at least one route")
        route_evaluations: list[list[tuple[RouteEvaluation, float, float]]] = []
        for candidate in ordered:
            row = []
            for route in candidate.routes:
                evaluation = evaluate_route(candidate.component, self.materials, route, self.policy)
                row.append((evaluation, candidate.component.disassembly_energy_kwh + route.energy_kwh, route.risk))
            route_evaluations.append(row)
        best: RecoveryPlan | None = None
        feasible = 0
        evaluated = 0
        for combo in product(*route_evaluations):
            evaluated += 1
            evaluations = [entry[0] for entry in combo]
            process_cost = sum(item.total_cost for item in evaluations)
            energy = sum(entry[1] for entry in combo)
            risk_sum = sum(entry[2] for entry in combo)
            if constraints.max_process_cost is not None and process_cost > constraints.max_process_cost:
                continue
            if constraints.max_energy_kwh is not None and energy > constraints.max_energy_kwh:
                continue
            if constraints.max_risk_sum is not None and risk_sum > constraints.max_risk_sum:
                continue
            feasible += 1
            plan = RecoveryPlan(evaluations=list(evaluations))
            if best is None or plan.total_score > best.total_score:
                best = plan
            elif best is not None and plan.total_score == best.total_score and plan.modes() < best.modes():
                best = plan
        if best is None:
            raise ValueError("no feasible recovery combination")
        return GlobalOptimizationResult(best, feasible, evaluated)
