from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Material, RecoveryPlan
from .optimizer import Candidate, RecoveryOptimizer
from .scoring import ScoringPolicy, evaluate_route


@dataclass(frozen=True, slots=True)
class BaselineResult:
    name: str
    plan: RecoveryPlan


def _select_by_metric(
    candidates: tuple[Candidate, ...],
    materials: dict[str, Material],
    policy: ScoringPolicy,
    *,
    metric: str,
) -> RecoveryPlan:
    chosen = []
    for candidate in candidates:
        evaluations = [evaluate_route(candidate.component, materials, route, policy) for route in candidate.routes]
        if metric == "mass":
            evaluations.sort(key=lambda item: (-item.retained_mass_kg, item.total_cost, item.mode.value))
        elif metric == "value":
            evaluations.sort(key=lambda item: (-item.recovered_value, item.total_cost, item.mode.value))
        else:
            raise ValueError(f"unknown baseline metric: {metric}")
        chosen.append(evaluations[0])
    return RecoveryPlan(evaluations=chosen)


def compare_baselines(
    candidates: Iterable[Candidate],
    materials: dict[str, Material],
    policy: ScoringPolicy | None = None,
) -> tuple[BaselineResult, ...]:
    """Compare the canonical policy against transparent counterfactual baselines."""
    policy = policy or ScoringPolicy()
    ordered = tuple(sorted(candidates, key=lambda c: c.component.component_id))
    if any(not candidate.routes for candidate in ordered):
        raise ValueError("every candidate must expose at least one route")

    ablated = ScoringPolicy(
        energy_shadow_price_per_kwh=policy.energy_shadow_price_per_kwh,
        risk_penalty=policy.risk_penalty,
        preservation_bonus=0.0,
        future_cycle_weight=0.0,
    )
    return (
        BaselineResult("canonical", RecoveryOptimizer(materials, policy).optimize(ordered)),
        BaselineResult("mass_only", _select_by_metric(ordered, materials, policy, metric="mass")),
        BaselineResult("value_only", _select_by_metric(ordered, materials, policy, metric="value")),
        BaselineResult("no_preservation_prior", RecoveryOptimizer(materials, ablated).optimize(ordered)),
    )
