"""Minimum-sufficient economic experiment primitives for Ω Value OS R2.

Experiments are plans/simulations.  They never mutate live prices or billing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple


@dataclass(frozen=True)
class ExperimentCandidate:
    name: str
    cost: float
    reversibility: float
    discrimination_power: float
    expected_information_gain: float
    risk: float = 0.0
    requires_human_approval: bool = False


@dataclass(frozen=True)
class PriceMutation:
    name: str
    relative_price: float
    pricing_model: str
    executable: bool = False


@dataclass(frozen=True)
class TournamentResult:
    mutation: PriceMutation
    metrics: Mapping[str, float]
    score: float


def minimum_sufficient_experiment(
    candidates: Iterable[ExperimentCandidate],
    *,
    minimum_discrimination: float,
    minimum_reversibility: float = 0.5,
    maximum_risk: float = 1.0,
) -> ExperimentCandidate | None:
    """Select the cheapest reversible experiment that can discriminate the claim."""
    eligible = [
        candidate
        for candidate in candidates
        if candidate.discrimination_power >= minimum_discrimination
        and candidate.reversibility >= minimum_reversibility
        and candidate.risk <= maximum_risk
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda candidate: (
            max(0.0, candidate.cost),
            -candidate.expected_information_gain,
            candidate.name,
        ),
    )


def experiment_option_value(candidate: ExperimentCandidate) -> float:
    """A bounded heuristic for deciding whether learning is worth buying."""
    benefit = max(0.0, candidate.expected_information_gain) * max(0.0, candidate.reversibility)
    burden = 1.0 + max(0.0, candidate.cost) + max(0.0, candidate.risk)
    return benefit / burden


def standard_price_mutations() -> Tuple[PriceMutation, ...]:
    """Return simulation-only mutations useful for pricing robustness tests."""
    return (
        PriceMutation("half_price", 0.5, "flat"),
        PriceMutation("lower_price", 0.8, "flat"),
        PriceMutation("baseline_price", 1.0, "flat"),
        PriceMutation("higher_price", 1.2, "flat"),
        PriceMutation("double_price", 2.0, "flat"),
        PriceMutation("usage_model", 1.0, "usage"),
        PriceMutation("subscription_model", 1.0, "subscription"),
    )


def pricing_tournament(
    outcomes: Mapping[str, Mapping[str, float]],
    mutations: Iterable[PriceMutation],
    *,
    weights: Mapping[str, float] | None = None,
) -> Tuple[TournamentResult, ...]:
    """Rank simulated/observed outcomes; never execute or publish a mutation."""
    metric_weights = dict(
        weights
        or {
            "verified_value": 1.0,
            "retention": 1.0,
            "margin": 1.0,
            "trust": 1.0,
            "conversion": 0.5,
            "risk": -1.0,
        }
    )
    results = []
    for mutation in mutations:
        metrics = dict(outcomes.get(mutation.name, {}))
        score = sum(metric_weights.get(key, 0.0) * float(value) for key, value in metrics.items())
        results.append(TournamentResult(mutation=mutation, metrics=metrics, score=score))
    return tuple(sorted(results, key=lambda result: (-result.score, result.mutation.name)))
