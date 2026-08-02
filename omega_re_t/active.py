"""Active experiment planning for finite deterministic hypothesis spaces."""

from __future__ import annotations

from collections import defaultdict
from itertools import product
from math import log2
from typing import Iterable, Mapping, Sequence

from .fsm import MealyMachine
from .models import Experiment, RiskClass


def candidate_sequences(alphabet: Sequence[str], *, max_length: int) -> Iterable[tuple[str, ...]]:
    if max_length <= 0:
        raise ValueError("max_length must be positive")
    for length in range(1, max_length + 1):
        yield from product(alphabet, repeat=length)


def output_partition(
    candidates: Sequence[MealyMachine],
    inputs: Sequence[str],
) -> dict[tuple[str, ...], tuple[str, ...]]:
    buckets: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for candidate in candidates:
        outputs, _ = candidate.run(inputs)
        buckets[outputs].append(candidate.candidate_id)
    return {outputs: tuple(ids) for outputs, ids in buckets.items()}


def expected_information_gain_bits(
    candidates: Sequence[MealyMachine],
    inputs: Sequence[str],
    *,
    posterior: Mapping[str, float] | None = None,
) -> float:
    if not candidates:
        return 0.0
    if posterior is None:
        probabilities = {candidate.candidate_id: 1.0 / len(candidates) for candidate in candidates}
    else:
        total = sum(max(0.0, posterior.get(candidate.candidate_id, 0.0)) for candidate in candidates)
        if total <= 0.0:
            raise ValueError("Posterior mass over candidates must be positive")
        probabilities = {
            candidate.candidate_id: max(0.0, posterior.get(candidate.candidate_id, 0.0)) / total
            for candidate in candidates
        }
    initial_entropy = -sum(value * log2(value) for value in probabilities.values() if value > 0.0)
    buckets: dict[tuple[str, ...], list[MealyMachine]] = defaultdict(list)
    for candidate in candidates:
        outputs, _ = candidate.run(inputs)
        buckets[outputs].append(candidate)
    expected_remaining = 0.0
    for bucket in buckets.values():
        mass = sum(probabilities[candidate.candidate_id] for candidate in bucket)
        if mass <= 0.0:
            continue
        conditional = [probabilities[candidate.candidate_id] / mass for candidate in bucket]
        entropy = -sum(value * log2(value) for value in conditional if value > 0.0)
        expected_remaining += mass * entropy
    return max(0.0, initial_entropy - expected_remaining)


def select_experiment(
    candidates: Sequence[MealyMachine],
    *,
    alphabet: Sequence[str],
    max_length: int,
    posterior: Mapping[str, float] | None = None,
    cost_per_symbol: float = 0.01,
    risk: RiskClass = RiskClass.MINIMAL,
    legal_penalty: float = 0.0,
    risk_penalty: float = 0.0,
) -> Experiment | None:
    if len(candidates) <= 1:
        return None
    best: Experiment | None = None
    for sequence in candidate_sequences(alphabet, max_length=max_length):
        gain = expected_information_gain_bits(candidates, sequence, posterior=posterior)
        partition_count = len(output_partition(candidates, sequence))
        cost = cost_per_symbol * len(sequence)
        utility = gain - cost - legal_penalty - risk_penalty
        experiment = Experiment(
            inputs=tuple(sequence),
            expected_information_gain_bits=gain,
            expected_partition_count=partition_count,
            cost=cost,
            risk=risk,
            legal_penalty=legal_penalty,
            utility=utility,
        )
        ordering = (
            experiment.utility,
            experiment.expected_information_gain_bits,
            -len(experiment.inputs),
            tuple(reversed(experiment.inputs)),
        )
        if best is None:
            best = experiment
            best_ordering = ordering
        elif ordering > best_ordering:
            best = experiment
            best_ordering = ordering
    return best
