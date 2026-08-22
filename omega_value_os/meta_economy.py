"""Bounded meta-economic compilation for Ω Value OS R2.

This module searches a finite design space of economic mechanisms.  It produces
candidates and rankings only: it cannot charge, publish prices, transfer funds,
or approve its own output.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Tuple

from .engine import meta_stop_rule


@dataclass(frozen=True)
class EconomicGenome:
    """Provider-neutral description of an economic mechanism."""

    name: str
    actors: Tuple[str, ...]
    value_objects: Tuple[str, ...]
    capabilities: Tuple[str, ...]
    evidence: Tuple[str, ...]
    exchange_mechanisms: Tuple[str, ...]
    pricing_mechanisms: Tuple[str, ...]
    revenue_mechanisms: Tuple[str, ...]
    capital_sources: Tuple[str, ...] = ()
    incentives: Tuple[str, ...] = ()
    governance: Tuple[str, ...] = ()
    memory: Tuple[str, ...] = ()
    falsifiers: Tuple[str, ...] = ()
    complexity_debt: float = 0.0
    risk_debt: float = 0.0
    is_no_action: bool = False


@dataclass(frozen=True)
class RepresentationCandidate:
    name: str
    expected_discrimination_gain: float
    reuse_gain: float
    complexity_cost: float
    evidence_debt: float = 0.0

    @property
    def score(self) -> float:
        numerator = max(0.0, self.expected_discrimination_gain) + max(0.0, self.reuse_gain)
        denominator = 1.0 + max(0.0, self.complexity_cost) + max(0.0, self.evidence_debt)
        return numerator / denominator


@dataclass(frozen=True)
class MetaEconomicCandidate:
    parent: EconomicGenome
    child: EconomicGenome
    mutation: str
    meta_depth: int
    requires_independent_evaluation: bool = True
    executable: bool = False


def no_action_genome() -> EconomicGenome:
    return EconomicGenome(
        name="NO_ACTION",
        actors=(),
        value_objects=(),
        capabilities=(),
        evidence=(),
        exchange_mechanisms=(),
        pricing_mechanisms=(),
        revenue_mechanisms=(),
        governance=("preserve_current_state",),
        falsifiers=("inaction_cost_exceeds_test_cost",),
        is_no_action=True,
    )


def compile_economic_genomes(
    seed: EconomicGenome,
    variations: Iterable[dict],
    *,
    max_candidates: int = 32,
) -> Tuple[EconomicGenome, ...]:
    """Compile a finite population and always retain a NO_ACTION baseline."""
    if max_candidates < 2:
        raise ValueError("max_candidates must be at least 2 to preserve NO_ACTION")

    population = [no_action_genome(), seed]
    allowed_fields = set(EconomicGenome.__dataclass_fields__)
    for variation in variations:
        if len(population) >= max_candidates:
            break
        safe = {key: value for key, value in variation.items() if key in allowed_fields}
        population.append(replace(seed, **safe))
    return tuple(population)


def representation_tournament(
    candidates: Iterable[RepresentationCandidate],
) -> Tuple[RepresentationCandidate, ...]:
    """Rank representations without asserting that the winner is true."""
    return tuple(sorted(candidates, key=lambda candidate: (-candidate.score, candidate.name)))


def mutate_economic_genome(
    parent: EconomicGenome,
    *,
    mutation: str,
    changes: dict,
    meta_depth: int = 1,
) -> MetaEconomicCandidate:
    """Generate a child candidate with no execution or promotion authority."""
    if meta_depth < 1:
        raise ValueError("meta_depth must be >= 1")
    allowed_fields = set(EconomicGenome.__dataclass_fields__)
    safe = {key: value for key, value in changes.items() if key in allowed_fields}
    child = replace(parent, **safe)
    return MetaEconomicCandidate(
        parent=parent,
        child=child,
        mutation=mutation,
        meta_depth=meta_depth,
    )


def meta_generation_allowed(
    *,
    verified_gain: float,
    complexity_debt: float,
    risk_debt: float,
    meta_depth: int,
    max_meta_depth: int = 4,
) -> bool:
    """Bound recursive generation by both evidence gain and an explicit depth cap."""
    if meta_depth >= max_meta_depth:
        return False
    return not meta_stop_rule(verified_gain, complexity_debt, risk_debt)
