"""Timed finite-state models with explicit latency uncertainty."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, pi, sqrt
from random import Random
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class LatencyModel:
    mean: float
    std: float
    minimum: float = 0.0
    maximum: float | None = None

    def __post_init__(self) -> None:
        if self.mean < 0 or self.std <= 0 or self.minimum < 0:
            raise ValueError("latency parameters must be positive")
        if self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("maximum must be >= minimum")

    def log_density(
        self,
        value: float,
        *,
        floor: float = 1.0e-300,
    ) -> float:
        if value < self.minimum or (
            self.maximum is not None and value > self.maximum
        ):
            return log(floor)
        z_score = (value - self.mean) / self.std
        density = (
            exp(-0.5 * z_score * z_score)
            / (self.std * sqrt(2 * pi))
        )
        return log(max(floor, density))

    def sample(self, generator: Random) -> float:
        for _ in range(1000):
            value = generator.gauss(self.mean, self.std)
            if value >= self.minimum and (
                self.maximum is None or value <= self.maximum
            ):
                return value
        return min(
            max(self.mean, self.minimum),
            self.maximum if self.maximum is not None else self.mean,
        )


@dataclass(frozen=True, slots=True)
class TimedTransition:
    next_state: str
    output: str
    latency: LatencyModel


@dataclass(frozen=True, slots=True)
class TimedObservation:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    latencies: tuple[float, ...]

    def __post_init__(self) -> None:
        if not (
            len(self.inputs)
            == len(self.outputs)
            == len(self.latencies)
        ):
            raise ValueError("timed observation lengths must match")
        if any(value < 0 for value in self.latencies):
            raise ValueError("latencies cannot be negative")


class TimedMealyMachine:
    def __init__(
        self,
        machine_id: str,
        states: Sequence[str],
        alphabet: Sequence[str],
        transitions: Mapping[tuple[str, str], TimedTransition],
        *,
        initial_state: str,
    ):
        self.machine_id = machine_id
        self.states = tuple(states)
        self.alphabet = tuple(alphabet)
        self.transitions = dict(transitions)
        self.initial_state = initial_state
        if initial_state not in self.states:
            raise ValueError("initial state missing")
        expected = {
            (state, symbol)
            for state in self.states
            for symbol in self.alphabet
        }
        if set(self.transitions) != expected:
            raise ValueError("transition table must be complete")
        if any(
            transition.next_state not in self.states
            for transition in self.transitions.values()
        ):
            raise ValueError("unknown next state")

    def predict(
        self,
        inputs: Sequence[str],
    ) -> tuple[tuple[str, ...], tuple[float, ...]]:
        state = self.initial_state
        outputs: list[str] = []
        means: list[float] = []
        for symbol in inputs:
            transition = self.transitions[(state, symbol)]
            outputs.append(transition.output)
            means.append(transition.latency.mean)
            state = transition.next_state
        return tuple(outputs), tuple(means)

    def sample(
        self,
        inputs: Sequence[str],
        *,
        seed: int = 0,
    ) -> TimedObservation:
        generator = Random(seed)
        state = self.initial_state
        outputs: list[str] = []
        latencies: list[float] = []
        for symbol in inputs:
            transition = self.transitions[(state, symbol)]
            outputs.append(transition.output)
            latencies.append(transition.latency.sample(generator))
            state = transition.next_state
        return TimedObservation(
            tuple(inputs),
            tuple(outputs),
            tuple(latencies),
        )

    def log_likelihood(
        self,
        observation: TimedObservation,
        *,
        output_error: float = 1.0e-6,
    ) -> float:
        if not 0 < output_error < 0.5:
            raise ValueError("output_error must be in (0, .5)")
        state = self.initial_state
        total = 0.0
        for symbol, output, latency in zip(
            observation.inputs,
            observation.outputs,
            observation.latencies,
        ):
            transition = self.transitions[(state, symbol)]
            total += log(
                1 - output_error
                if transition.output == output
                else output_error
            )
            total += transition.latency.log_density(latency)
            state = transition.next_state
        return total


def temporal_separation(
    left: TimedMealyMachine,
    right: TimedMealyMachine,
    inputs: Sequence[str],
) -> float:
    left_outputs, left_means = left.predict(inputs)
    right_outputs, right_means = right.predict(inputs)
    output_distance = sum(
        left_output != right_output
        for left_output, right_output in zip(
            left_outputs,
            right_outputs,
        )
    )
    latency_distance = sum(
        abs(left_mean - right_mean)
        for left_mean, right_mean in zip(
            left_means,
            right_means,
        )
    )
    return float(output_distance) + latency_distance


def choose_temporal_experiment(
    candidates: Sequence[TimedMealyMachine],
    experiments: Sequence[Sequence[str]],
    *,
    cost_per_symbol: float = 0.01,
) -> tuple[str, ...] | None:
    if len(candidates) < 2:
        return None
    best: tuple[float, int, tuple[str, ...]] | None = None
    for raw in experiments:
        inputs = tuple(raw)
        pairwise: list[float] = []
        for index, left in enumerate(candidates):
            for right in candidates[index + 1 :]:
                pairwise.append(
                    temporal_separation(left, right, inputs)
                )
        score = (
            min(pairwise, default=0.0)
            - cost_per_symbol * len(inputs),
            -len(inputs),
            inputs,
        )
        if best is None or score > best:
            best = score
    return None if best is None else best[2]


def demo_timed_pair() -> tuple[
    TimedMealyMachine,
    TimedMealyMachine,
]:
    states = ("idle", "armed")
    alphabet = ("A", "B")
    left_transitions = {
        ("idle", "A"): TimedTransition(
            "armed",
            "0",
            LatencyModel(0.10, 0.01),
        ),
        ("idle", "B"): TimedTransition(
            "idle",
            "0",
            LatencyModel(0.20, 0.02),
        ),
        ("armed", "A"): TimedTransition(
            "armed",
            "1",
            LatencyModel(0.12, 0.01),
        ),
        ("armed", "B"): TimedTransition(
            "idle",
            "1",
            LatencyModel(0.30, 0.02),
        ),
    }
    right_transitions = dict(left_transitions)
    right_transitions[("armed", "B")] = TimedTransition(
        "idle",
        "1",
        LatencyModel(0.55, 0.02),
    )
    return (
        TimedMealyMachine(
            "timed-left",
            states,
            alphabet,
            left_transitions,
            initial_state="idle",
        ),
        TimedMealyMachine(
            "timed-right",
            states,
            alphabet,
            right_transitions,
            initial_state="idle",
        ),
    )
