"""Revenue portfolio metrics for active/passive/mixed monetization.

Metrics are descriptive decision aids, not causal proof or financial advice.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .models import RevenueMode

EPSILON = 1e-9


@dataclass(frozen=True)
class RevenueStreamMetrics:
    name: str
    mode: RevenueMode
    gross_revenue: float
    direct_cost: float
    marginal_hours: float
    platform: str
    recurring_fraction: float = 0.0
    trust_delta: float = 0.0
    maintenance_burden: float = 0.0

    @property
    def contribution_margin(self) -> float:
        return self.gross_revenue - self.direct_cost

    @property
    def passive_leverage_ratio(self) -> float:
        recurring_revenue = max(0.0, self.gross_revenue) * max(
            0.0, min(1.0, self.recurring_fraction)
        )
        return recurring_revenue / max(EPSILON, max(0.0, self.marginal_hours))


def platform_concentration(streams: Iterable[RevenueStreamMetrics]) -> float:
    """HHI-like concentration over positive contribution margin by platform."""
    margins = {}
    for stream in streams:
        margin = max(0.0, stream.contribution_margin)
        margins[stream.platform] = margins.get(stream.platform, 0.0) + margin
    total = sum(margins.values())
    if total <= EPSILON:
        return 0.0
    shares = (value / total for value in margins.values())
    return sum(share * share for share in shares)


def revenue_mode_mix(streams: Iterable[RevenueStreamMetrics]) -> Tuple[float, float, float]:
    """Return positive-margin shares for active, passive, mixed modes."""
    totals = {mode: 0.0 for mode in RevenueMode}
    for stream in streams:
        totals[stream.mode] += max(0.0, stream.contribution_margin)
    total = sum(totals.values())
    if total <= EPSILON:
        return (0.0, 0.0, 0.0)
    return (
        totals[RevenueMode.ACTIVE] / total,
        totals[RevenueMode.PASSIVE] / total,
        totals[RevenueMode.MIXED] / total,
    )


def prune_candidates(streams: Iterable[RevenueStreamMetrics]) -> Tuple[str, ...]:
    """Flag dominated streams for review, never auto-delete them."""
    flagged = []
    for stream in streams:
        if stream.contribution_margin <= 0:
            flagged.append(stream.name)
        elif stream.trust_delta < 0 and stream.maintenance_burden >= 0.5:
            flagged.append(stream.name)
    return tuple(flagged)
