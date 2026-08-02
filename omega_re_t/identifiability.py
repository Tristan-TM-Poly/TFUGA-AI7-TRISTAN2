"""Behavioral equivalence and identifiability-debt calculations."""

from __future__ import annotations

from collections import defaultdict
from math import log2
from typing import Iterable, Mapping, Sequence

from .fsm import MealyMachine


def behavioral_signature(machine: MealyMachine, tests: Iterable[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(machine.run(test)[0] for test in tests)


def equivalence_classes(
    candidates: Sequence[MealyMachine],
    tests: Iterable[Sequence[str]],
) -> tuple[tuple[str, ...], ...]:
    materialized_tests = tuple(tuple(test) for test in tests)
    buckets: dict[tuple[tuple[str, ...], ...], list[str]] = defaultdict(list)
    for candidate in candidates:
        buckets[behavioral_signature(candidate, materialized_tests)].append(candidate.candidate_id)
    return tuple(tuple(sorted(ids)) for ids in buckets.values())


def identifiability_debt_bits(
    candidates: Sequence[MealyMachine],
    tests: Iterable[Sequence[str]],
    *,
    posterior: Mapping[str, float] | None = None,
) -> float:
    if len(candidates) <= 1:
        return 0.0
    classes = equivalence_classes(candidates, tests)
    if posterior is None:
        probability = {candidate.candidate_id: 1.0 / len(candidates) for candidate in candidates}
    else:
        total = sum(max(0.0, posterior.get(candidate.candidate_id, 0.0)) for candidate in candidates)
        if total <= 0.0:
            raise ValueError("Posterior mass must be positive")
        probability = {
            candidate.candidate_id: max(0.0, posterior.get(candidate.candidate_id, 0.0)) / total
            for candidate in candidates
        }
    debt = 0.0
    for equivalence_class in classes:
        mass = sum(probability[candidate_id] for candidate_id in equivalence_class)
        if mass <= 0.0:
            continue
        conditional = [probability[candidate_id] / mass for candidate_id in equivalence_class]
        debt += mass * -sum(value * log2(value) for value in conditional if value > 0.0)
    return debt
