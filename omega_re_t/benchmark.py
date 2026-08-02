"""Deterministic OAKBench for active versus passive FSM reconstruction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from random import Random
from statistics import mean
from typing import Sequence

from .active import select_experiment
from .bayes import posterior_map, score_candidates
from .fsm import MealyMachine
from .models import Observation


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    seed: int
    active_rounds_to_unique: int | None
    passive_rounds_to_unique: int | None
    active_symbols: int
    passive_symbols: int


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    cases: int
    active_success_rate: float
    passive_success_rate: float
    mean_active_rounds: float
    mean_passive_rounds: float
    mean_active_symbols: float
    mean_passive_symbols: float
    rows: tuple[BenchmarkRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            **{key: value for key, value in asdict(self).items() if key != "rows"},
            "rows": [asdict(row) for row in self.rows],
        }


def _tests(alphabet: Sequence[str], max_length: int) -> tuple[tuple[str, ...], ...]:
    return tuple(
        sequence
        for length in range(1, max_length + 1)
        for sequence in product(alphabet, repeat=length)
    )


def _identified_behavior(
    oracle: MealyMachine,
    candidates: Sequence[MealyMachine],
    *,
    max_length: int,
) -> bool:
    if not candidates:
        return False
    tests = _tests(oracle.input_alphabet, max_length)
    oracle_signature = tuple(oracle.run(test)[0] for test in tests)
    return all(tuple(candidate.run(test)[0] for test in tests) == oracle_signature for candidate in candidates)


def _filter(candidates: Sequence[MealyMachine], observations: Sequence[Observation]) -> list[MealyMachine]:
    return [candidate for candidate in candidates if candidate.is_consistent(observations)]


def _active_trial(
    oracle: MealyMachine,
    candidates: Sequence[MealyMachine],
    *,
    max_rounds: int,
    max_length: int,
) -> tuple[int | None, int]:
    observations: list[Observation] = []
    surviving = list(candidates)
    symbols = 0
    if _identified_behavior(oracle, surviving, max_length=max_length):
        return 0, 0
    for round_index in range(1, max_rounds + 1):
        scores = score_candidates(surviving, observations)
        experiment = select_experiment(
            surviving,
            alphabet=oracle.input_alphabet,
            max_length=max_length,
            posterior=posterior_map(scores),
        )
        if experiment is None:
            return round_index - 1, symbols
        observation = oracle.observe(experiment.inputs)
        observations.append(observation)
        symbols += len(experiment.inputs)
        surviving = _filter(surviving, observations)
        if _identified_behavior(oracle, surviving, max_length=max_length):
            return round_index, symbols
    return None, symbols


def _passive_trial(
    oracle: MealyMachine,
    candidates: Sequence[MealyMachine],
    *,
    seed: int,
    max_rounds: int,
    max_length: int,
) -> tuple[int | None, int]:
    rng = Random(seed)
    observations: list[Observation] = []
    surviving = list(candidates)
    symbols = 0
    if _identified_behavior(oracle, surviving, max_length=max_length):
        return 0, 0
    for round_index in range(1, max_rounds + 1):
        length = rng.randint(1, max_length)
        inputs = tuple(rng.choice(oracle.input_alphabet) for _ in range(length))
        observation = oracle.observe(inputs)
        observations.append(observation)
        symbols += length
        surviving = _filter(surviving, observations)
        if _identified_behavior(oracle, surviving, max_length=max_length):
            return round_index, symbols
    return None, symbols


def run_benchmark(
    candidates: Sequence[MealyMachine],
    *,
    seeds: Sequence[int] = tuple(range(16)),
    max_rounds: int = 12,
    max_length: int = 5,
) -> BenchmarkSummary:
    if not candidates:
        raise ValueError("candidates cannot be empty")
    rows: list[BenchmarkRow] = []
    for seed in seeds:
        oracle = candidates[seed % len(candidates)]
        active_rounds, active_symbols = _active_trial(
            oracle,
            candidates,
            max_rounds=max_rounds,
            max_length=max_length,
        )
        passive_rounds, passive_symbols = _passive_trial(
            oracle,
            candidates,
            seed=seed,
            max_rounds=max_rounds,
            max_length=max_length,
        )
        rows.append(
            BenchmarkRow(
                seed=seed,
                active_rounds_to_unique=active_rounds,
                passive_rounds_to_unique=passive_rounds,
                active_symbols=active_symbols,
                passive_symbols=passive_symbols,
            )
        )
    active_successes = [row for row in rows if row.active_rounds_to_unique is not None]
    passive_successes = [row for row in rows if row.passive_rounds_to_unique is not None]
    return BenchmarkSummary(
        cases=len(rows),
        active_success_rate=len(active_successes) / len(rows),
        passive_success_rate=len(passive_successes) / len(rows),
        mean_active_rounds=mean(row.active_rounds_to_unique for row in active_successes) if active_successes else 0.0,
        mean_passive_rounds=mean(row.passive_rounds_to_unique for row in passive_successes) if passive_successes else 0.0,
        mean_active_symbols=mean(row.active_symbols for row in rows),
        mean_passive_symbols=mean(row.passive_symbols for row in rows),
        rows=tuple(rows),
    )
