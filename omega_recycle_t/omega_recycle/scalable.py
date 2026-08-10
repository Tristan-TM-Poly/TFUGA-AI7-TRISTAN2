from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .flows import FlowConstraints
from .models import Material, RecoveryPlan, RouteEvaluation
from .optimizer import Candidate
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class SearchBudget:
    """Hard search budget for branch-and-bound.

    A finite budget can return an incumbent without an optimality certificate.
    """

    max_nodes: int | None = 100_000

    def __post_init__(self) -> None:
        if self.max_nodes is not None and self.max_nodes <= 0:
            raise ValueError("max_nodes must be positive or None")


@dataclass(frozen=True, slots=True)
class ScalableOptimizationResult:
    plan: RecoveryPlan
    search_complete: bool
    evaluated_nodes: int
    feasible_leaves: int
    pruned_by_bound: int
    pruned_by_constraints: int
    root_upper_bound: float
    optimality_gap_upper_bound: float

    @property
    def optimality_certified(self) -> bool:
        return self.search_complete


class BranchAndBoundRecoveryOptimizer:
    """Auditable branch-and-bound solver compatible with the R0.2 exact oracle.

    The score upper bound ignores coupling constraints, so it is admissible.
    Search is still exponential in the worst case; when ``SearchBudget`` is
    exhausted the best incumbent is returned without an optimality certificate.
    """

    def __init__(self, materials: dict[str, Material], policy: ScoringPolicy | None = None) -> None:
        self.materials = materials
        self.policy = policy or ScoringPolicy()

    def optimize(
        self,
        candidates: Iterable[Candidate],
        constraints: FlowConstraints,
        *,
        budget: SearchBudget | None = None,
    ) -> ScalableOptimizationResult:
        budget = budget or SearchBudget()
        ordered = tuple(sorted(candidates, key=lambda c: c.component.component_id))
        if any(not candidate.routes for candidate in ordered):
            raise ValueError("every candidate must expose at least one route")

        rows: list[list[tuple[RouteEvaluation, float, float]]] = []
        for candidate in ordered:
            row: list[tuple[RouteEvaluation, float, float]] = []
            for route in candidate.routes:
                evaluation = evaluate_route(candidate.component, self.materials, route, self.policy)
                energy = candidate.component.disassembly_energy_kwh + route.energy_kwh
                row.append((evaluation, energy, route.risk))
            row.sort(key=lambda entry: (-entry[0].score, entry[0].mode.value))
            rows.append(row)

        suffix_best = [0.0] * (len(rows) + 1)
        for index in range(len(rows) - 1, -1, -1):
            suffix_best[index] = suffix_best[index + 1] + max(entry[0].score for entry in rows[index])
        root_upper_bound = suffix_best[0]

        incumbent: RecoveryPlan | None = None
        evaluated_nodes = 0
        feasible_leaves = 0
        pruned_by_bound = 0
        pruned_by_constraints = 0
        exhausted = False

        def violates(cost: float, energy: float, risk: float) -> bool:
            if constraints.max_process_cost is not None and cost > constraints.max_process_cost:
                return True
            if constraints.max_energy_kwh is not None and energy > constraints.max_energy_kwh:
                return True
            if constraints.max_risk_sum is not None and risk > constraints.max_risk_sum:
                return True
            return False

        def better(plan: RecoveryPlan, current: RecoveryPlan | None) -> bool:
            if current is None:
                return True
            if plan.total_score > current.total_score + 1e-12:
                return True
            return abs(plan.total_score - current.total_score) <= 1e-12 and plan.modes() < current.modes()

        def dfs(
            index: int,
            chosen: list[RouteEvaluation],
            cost: float,
            energy: float,
            risk: float,
            score: float,
        ) -> None:
            nonlocal incumbent, evaluated_nodes, feasible_leaves
            nonlocal pruned_by_bound, pruned_by_constraints, exhausted

            if budget.max_nodes is not None and evaluated_nodes >= budget.max_nodes:
                exhausted = True
                return
            evaluated_nodes += 1

            optimistic = score + suffix_best[index]
            if incumbent is not None and optimistic < incumbent.total_score - 1e-12:
                pruned_by_bound += 1
                return

            if index == len(rows):
                feasible_leaves += 1
                plan = RecoveryPlan(evaluations=list(chosen))
                if better(plan, incumbent):
                    incumbent = plan
                return

            for evaluation, route_energy, route_risk in rows[index]:
                next_cost = cost + evaluation.total_cost
                next_energy = energy + route_energy
                next_risk = risk + route_risk
                if violates(next_cost, next_energy, next_risk):
                    pruned_by_constraints += 1
                    continue
                dfs(
                    index + 1,
                    chosen + [evaluation],
                    next_cost,
                    next_energy,
                    next_risk,
                    score + evaluation.score,
                )
                if exhausted:
                    return

        dfs(0, [], 0.0, 0.0, 0.0, 0.0)

        if incumbent is None:
            if exhausted:
                raise ValueError("search budget exhausted before a feasible plan was found")
            raise ValueError("no feasible recovery combination")

        search_complete = not exhausted
        gap = 0.0 if search_complete else max(0.0, root_upper_bound - incumbent.total_score)
        return ScalableOptimizationResult(
            plan=incumbent,
            search_complete=search_complete,
            evaluated_nodes=evaluated_nodes,
            feasible_leaves=feasible_leaves,
            pruned_by_bound=pruned_by_bound,
            pruned_by_constraints=pruned_by_constraints,
            root_upper_bound=root_upper_bound,
            optimality_gap_upper_bound=gap,
        )
