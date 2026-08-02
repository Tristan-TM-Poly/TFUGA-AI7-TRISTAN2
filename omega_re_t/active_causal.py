"""Bounded active intervention selection over explicit Bernoulli hypotheses."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


def _binary_entropy(p: float) -> float:
    if p < 0.0 or p > 1.0 or not math.isfinite(p):
        raise ValueError("probability must lie in [0, 1]")
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


@dataclass(frozen=True)
class CausalHypothesis:
    name: str
    outcome_probability: Mapping[str, float]
    prior: float = 1.0

    def probability(self, intervention: str) -> float:
        try:
            value = float(self.outcome_probability[intervention])
        except KeyError as exc:
            raise KeyError(f"hypothesis {self.name!r} lacks intervention {intervention!r}") from exc
        if not 0.0 <= value <= 1.0 or not math.isfinite(value):
            raise ValueError("outcome probabilities must lie in [0, 1]")
        return value


@dataclass(frozen=True)
class Intervention:
    name: str
    cost: float = 1.0
    authorized: bool = True
    reversible: bool = True
    risk: float = 0.0


@dataclass(frozen=True)
class InterventionScore:
    intervention: str
    information_gain_bits: float
    predictive_entropy_bits: float
    utility: float
    blocked: bool
    blockers: tuple[str, ...]


def normalize_priors(hypotheses: Sequence[CausalHypothesis]) -> tuple[float, ...]:
    if not hypotheses:
        raise ValueError("hypotheses cannot be empty")
    priors = [float(item.prior) for item in hypotheses]
    if any((not math.isfinite(value) or value < 0.0) for value in priors):
        raise ValueError("priors must be finite and non-negative")
    total = sum(priors)
    if total <= 0.0:
        raise ValueError("prior total must be positive")
    return tuple(value / total for value in priors)


def score_intervention(
    hypotheses: Sequence[CausalHypothesis],
    intervention: Intervention,
    *,
    risk_penalty: float = 1.0,
) -> InterventionScore:
    priors = normalize_priors(hypotheses)
    blockers: list[str] = []
    if not intervention.authorized:
        blockers.append("authorization_missing")
    if not intervention.reversible:
        blockers.append("intervention_not_reversible")
    if intervention.cost <= 0.0 or not math.isfinite(intervention.cost):
        blockers.append("invalid_cost")

    p_one = sum(
        prior * hypothesis.probability(intervention.name)
        for prior, hypothesis in zip(priors, hypotheses, strict=True)
    )
    predictive_entropy = _binary_entropy(p_one)
    expected_conditional = sum(
        prior * _binary_entropy(hypothesis.probability(intervention.name))
        for prior, hypothesis in zip(priors, hypotheses, strict=True)
    )
    information_gain = max(0.0, predictive_entropy - expected_conditional)
    utility = -math.inf if blockers else information_gain / intervention.cost - risk_penalty * intervention.risk
    return InterventionScore(
        intervention=intervention.name,
        information_gain_bits=information_gain,
        predictive_entropy_bits=predictive_entropy,
        utility=utility,
        blocked=bool(blockers),
        blockers=tuple(blockers),
    )


def select_intervention(
    hypotheses: Sequence[CausalHypothesis],
    interventions: Sequence[Intervention],
    *,
    risk_penalty: float = 1.0,
) -> InterventionScore:
    if not interventions:
        raise ValueError("interventions cannot be empty")
    scores = [score_intervention(hypotheses, item, risk_penalty=risk_penalty) for item in interventions]
    allowed = [score for score in scores if not score.blocked]
    if not allowed:
        raise ValueError("all interventions are blocked")
    return max(allowed, key=lambda score: (score.utility, score.information_gain_bits, score.intervention))


def update_posterior(
    hypotheses: Sequence[CausalHypothesis],
    intervention: str,
    observed_one: bool,
) -> tuple[float, ...]:
    priors = normalize_priors(hypotheses)
    likelihoods = [
        hypothesis.probability(intervention) if observed_one else 1.0 - hypothesis.probability(intervention)
        for hypothesis in hypotheses
    ]
    unnormalized = [prior * likelihood for prior, likelihood in zip(priors, likelihoods, strict=True)]
    total = sum(unnormalized)
    if total <= 0.0:
        raise ValueError("observation has zero probability under every hypothesis")
    return tuple(value / total for value in unnormalized)
