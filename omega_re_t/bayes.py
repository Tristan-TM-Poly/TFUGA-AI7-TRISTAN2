"""Bayesian scoring with explicit deterministic-noise assumptions."""

from __future__ import annotations

from math import exp, log, log2
from typing import Iterable, Mapping, Sequence

from .fsm import MealyMachine
from .models import CandidateScore, Observation


def log_likelihood(
    candidate: MealyMachine,
    observations: Sequence[Observation],
    *,
    error_probability: float = 1.0e-6,
) -> tuple[float, int]:
    if not 0.0 < error_probability < 0.5:
        raise ValueError("error_probability must be in (0, 0.5)")
    matches = 0
    mismatches = 0
    for observation in observations:
        predicted, _ = candidate.run(observation.inputs)
        for expected, actual in zip(predicted, observation.outputs):
            if expected == actual:
                matches += 1
            else:
                mismatches += 1
    value = matches * log(1.0 - error_probability) + mismatches * log(error_probability)
    return value, mismatches


def score_candidates(
    candidates: Iterable[MealyMachine],
    observations: Sequence[Observation],
    *,
    error_probability: float = 1.0e-6,
    complexity_penalty: float = 0.0,
    priors: Mapping[str, float] | None = None,
) -> tuple[CandidateScore, ...]:
    raw: list[tuple[MealyMachine, float, float, int]] = []
    for candidate in candidates:
        likelihood, mismatches = log_likelihood(
            candidate,
            observations,
            error_probability=error_probability,
        )
        prior = 1.0 if priors is None else float(priors.get(candidate.candidate_id, 0.0))
        if prior < 0.0:
            raise ValueError("Priors cannot be negative")
        if prior == 0.0:
            log_weight = float("-inf")
        else:
            log_weight = likelihood + log(prior) - complexity_penalty * candidate.complexity
        raw.append((candidate, log_weight, prior, mismatches))
    if not raw:
        return ()
    finite = [row[1] for row in raw if row[1] != float("-inf")]
    if not finite:
        raise ValueError("All candidates received zero prior probability")
    maximum = max(finite)
    weights = [0.0 if row[1] == float("-inf") else exp(row[1] - maximum) for row in raw]
    normalizer = sum(weights)
    return tuple(
        CandidateScore(
            candidate_id=candidate.candidate_id,
            log_likelihood=log_weight,
            prior=prior,
            posterior=weight / normalizer,
            complexity=candidate.complexity,
            mismatches=mismatches,
        )
        for (candidate, log_weight, prior, mismatches), weight in sorted(
            zip(raw, weights),
            key=lambda pair: pair[1],
            reverse=True,
        )
    )


def posterior_entropy_bits(scores: Sequence[CandidateScore]) -> float:
    return -sum(score.posterior * log2(score.posterior) for score in scores if score.posterior > 0.0)


def posterior_map(scores: Sequence[CandidateScore]) -> dict[str, float]:
    return {score.candidate_id: score.posterior for score in scores}
