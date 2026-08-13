"""Bounded portfolio optimization for engineering opportunity selection."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import itertools
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PortfolioOpportunity:
    opportunity_id: str
    expected_value: float
    effort_cost: float
    success_probability: float = 1.0


@dataclass(frozen=True)
class OptimizationPortfolioPlan:
    selected: tuple[str, ...]
    total_effort: float
    expected_value: float
    interaction_value: float
    status: str = "bounded-optimization-portfolio"
    oak_warning: str = (
        "Portfolio value is exact only for the supplied finite candidate set "
        "and supplied value/probability/interaction estimates. It is not a "
        "guarantee of realized engineering or financial return."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def optimize_portfolio(
    opportunities: Sequence[PortfolioOpportunity],
    *,
    effort_budget: float,
    interactions: Mapping[tuple[str, str], float] | None = None,
    max_candidates: int = 18,
) -> OptimizationPortfolioPlan:
    rows = tuple(opportunities)
    if effort_budget < 0:
        raise ValueError("effort_budget must be non-negative")
    if len(rows) > max_candidates:
        raise ValueError(f"exact subset search capped at {max_candidates} candidates")
    ids = [row.opportunity_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("opportunity ids must be unique")
    for row in rows:
        if row.effort_cost < 0 or row.expected_value < 0:
            raise ValueError("effort and expected value must be non-negative")
        if not 0.0 <= row.success_probability <= 1.0:
            raise ValueError("success_probability must be in [0, 1]")

    interactions = interactions or {}
    best_value = 0.0
    best_effort = 0.0
    best_chosen: tuple[str, ...] = ()
    best_pair_value = 0.0
    for size in range(len(rows) + 1):
        for subset in itertools.combinations(rows, size):
            effort = sum(row.effort_cost for row in subset)
            if effort > effort_budget + 1e-12:
                continue
            chosen = tuple(sorted(row.opportunity_id for row in subset))
            base_value = sum(row.expected_value * row.success_probability for row in subset)
            pair_value = 0.0
            for a, b in itertools.combinations(chosen, 2):
                pair_value += float(interactions.get((a, b), interactions.get((b, a), 0.0)))
            value = base_value + pair_value
            key = (value, -effort, chosen)
            best_key = (best_value, -best_effort, best_chosen)
            if key > best_key:
                best_value = value
                best_effort = effort
                best_chosen = chosen
                best_pair_value = pair_value

    return OptimizationPortfolioPlan(
        selected=best_chosen,
        total_effort=best_effort,
        expected_value=best_value,
        interaction_value=best_pair_value,
    )
