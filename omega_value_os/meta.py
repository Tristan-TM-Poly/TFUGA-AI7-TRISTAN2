"""Bounded meta-generation primitives for Ω Value OS.

This module generates *candidates*, never self-approves or executes them.
Generator != Judge != Authority is enforced structurally.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Tuple

from .engine import meta_stop_rule
from .models import StrategyGenome


@dataclass(frozen=True)
class GeneratorGenome:
    name: str
    objective: str
    operators: Tuple[str, ...]
    constraints: Tuple[str, ...]
    version: int = 1


@dataclass(frozen=True)
class MetaCandidate:
    parent: GeneratorGenome
    child: GeneratorGenome
    mutation: str
    requires_independent_evaluation: bool = True


def mutate_generator(parent: GeneratorGenome, mutation: str) -> MetaCandidate:
    """Create a traceable child candidate without promoting it."""
    child = replace(
        parent,
        name=f"{parent.name}@{parent.version + 1}",
        operators=parent.operators + (mutation,),
        version=parent.version + 1,
    )
    return MetaCandidate(parent=parent, child=child, mutation=mutation)


def strategy_population(seed: StrategyGenome, variations: Iterable[dict]) -> Tuple[StrategyGenome, ...]:
    """Produce a finite candidate population and always retain NO_ACTION baseline."""
    population = [seed]
    for variation in variations:
        allowed = {
            key: value
            for key, value in variation.items()
            if key in StrategyGenome.__dataclass_fields__
        }
        population.append(replace(seed, **allowed))
    return tuple(population)


def should_create_meta_layer(
    verified_gain: float,
    complexity_debt: float,
    risk_debt: float,
) -> bool:
    return not meta_stop_rule(verified_gain, complexity_debt, risk_debt)
