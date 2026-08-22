"""Minimal counterfactual market/shock simulator.

Outputs are scenario calculations, never forecasts or evidence that the future
will follow a simulated world.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class EconomicState:
    revenue: float
    costs: float
    churn: float
    platform_reach: float
    trust: float

    @property
    def operating_surplus(self) -> float:
        return self.revenue - self.costs


@dataclass(frozen=True)
class Shock:
    name: str
    revenue_factor: float = 1.0
    cost_factor: float = 1.0
    churn_factor: float = 1.0
    reach_factor: float = 1.0
    trust_delta: float = 0.0


@dataclass(frozen=True)
class ShockResult:
    shock: str
    before: EconomicState
    after: EconomicState
    surplus_delta: float


def apply_shock(state: EconomicState, shock: Shock) -> ShockResult:
    after = EconomicState(
        revenue=max(0.0, state.revenue * max(0.0, shock.revenue_factor)),
        costs=max(0.0, state.costs * max(0.0, shock.cost_factor)),
        churn=max(0.0, state.churn * max(0.0, shock.churn_factor)),
        platform_reach=max(0.0, state.platform_reach * max(0.0, shock.reach_factor)),
        trust=max(0.0, min(1.0, state.trust + shock.trust_delta)),
    )
    return ShockResult(
        shock=shock.name,
        before=state,
        after=after,
        surplus_delta=after.operating_surplus - state.operating_surplus,
    )


def shock_curriculum(state: EconomicState, shocks: Iterable[Shock]) -> Tuple[ShockResult, ...]:
    """Evaluate independent shocks from the same baseline state."""
    return tuple(apply_shock(state, shock) for shock in shocks)
