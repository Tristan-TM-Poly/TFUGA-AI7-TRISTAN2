"""Bayes-Tristan inspired strategy routing without truth-probability claims."""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import CampaignAllocation, StrategyScore


def update_strategy(
    strategy: StrategyScore,
    *,
    supportive_results: int = 0,
    refuting_results: int = 0,
) -> StrategyScore:
    if supportive_results < 0 or refuting_results < 0:
        raise ValueError("result counts must be non-negative")
    return replace(
        strategy,
        evidence_for=strategy.evidence_for + supportive_results,
        evidence_against=strategy.evidence_against + refuting_results,
    )


def rank_strategies(strategies: Iterable[StrategyScore]) -> tuple[StrategyScore, ...]:
    items = tuple(strategies)
    ids = [item.strategy_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("strategy ids must be unique")
    return tuple(sorted(items, key=lambda item: (-item.value, item.strategy_id)))


def allocate_finite_budget(
    strategies: Iterable[StrategyScore],
    *,
    total_budget_units: int,
) -> tuple[CampaignAllocation, ...]:
    if total_budget_units <= 0:
        raise ValueError("total_budget_units must be positive")
    ranked = rank_strategies(strategies)
    if not ranked:
        return ()
    values = [max(item.value, 1e-12) for item in ranked]
    total_value = sum(values)
    raw = [total_budget_units * value / total_value for value in values]
    floors = [int(value) for value in raw]
    remainder = total_budget_units - sum(floors)
    order = sorted(range(len(raw)), key=lambda index: (-(raw[index] - floors[index]), ranked[index].strategy_id))
    for index in order[:remainder]:
        floors[index] += 1
    allocations: list[CampaignAllocation] = []
    for rank, (strategy, units, value) in enumerate(zip(ranked, floors, values), start=1):
        allocations.append(
            CampaignAllocation(
                strategy_id=strategy.strategy_id,
                problem_id=strategy.problem_id,
                rank=rank,
                normalized_share=value / total_value,
                finite_budget_units=units,
                rationale=(
                    "routing score separates fertility, testability, formalizability, impact, cost and false-progress risk",
                    "posterior weight routes effort and is not a probability of mathematical truth",
                    "the current batch is finite; no permanent total campaign cap is asserted",
                ),
            )
        )
    return tuple(allocations)
