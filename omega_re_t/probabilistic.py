"""Probabilistic finite-state reconstruction primitives for Ω-RE-T∞ R0.2."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from math import exp, log, log2
from random import Random
from typing import Iterable, Mapping, Sequence


def _normalise(weights: Mapping[str, float]) -> dict[str, float]:
    if not weights:
        raise ValueError("distribution cannot be empty")
    if any(value < 0 for value in weights.values()):
        raise ValueError("weights cannot be negative")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("distribution must have positive mass")
    return {
        key: value / total
        for key, value in sorted(weights.items())
    }


@dataclass(frozen=True, slots=True)
class ProbabilisticTransition:
    next_state: str
    output_distribution: Mapping[str, float]
    next_state_distribution: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "output_distribution",
            _normalise(self.output_distribution),
        )
        if self.next_state_distribution is not None:
            object.__setattr__(
                self,
                "next_state_distribution",
                _normalise(self.next_state_distribution),
            )
            if self.next_state not in self.next_state_distribution:
                raise ValueError(
                    "nominal next_state must be in next_state_distribution"
                )


@dataclass(frozen=True, slots=True)
class ProbabilisticObservation:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    reset_before: bool = True
    weight: float = 1.0

    def __post_init__(self) -> None:
        if len(self.inputs) != len(self.outputs):
            raise ValueError("inputs and outputs must align")
        if self.weight <= 0:
            raise ValueError("weight must be positive")


class ProbabilisticMealyMachine:
    def __init__(
        self,
        machine_id: str,
        states: Sequence[str],
        alphabet: Sequence[str],
        transitions: Mapping[
            tuple[str, str],
            ProbabilisticTransition,
        ],
        *,
        initial_state: str,
    ):
        self.machine_id = machine_id
        self.states = tuple(states)
        self.alphabet = tuple(alphabet)
        self.transitions = dict(transitions)
        self.initial_state = initial_state
        if len(set(self.states)) != len(self.states) or not self.states:
            raise ValueError("states must be unique and non-empty")
        if len(set(self.alphabet)) != len(self.alphabet) or not self.alphabet:
            raise ValueError("alphabet must be unique and non-empty")
        if initial_state not in self.states:
            raise ValueError("initial_state must exist")
        expected = {
            (state, symbol)
            for state in self.states
            for symbol in self.alphabet
        }
        if set(self.transitions) != expected:
            raise ValueError("transition table must be complete")
        for transition in self.transitions.values():
            if transition.next_state not in self.states:
                raise ValueError("transition references unknown state")
            if (
                transition.next_state_distribution
                and not set(transition.next_state_distribution)
                <= set(self.states)
            ):
                raise ValueError(
                    "next-state distribution references unknown state"
                )

    @property
    def digest(self) -> str:
        canonical = {
            "machine_id": self.machine_id,
            "states": self.states,
            "alphabet": self.alphabet,
            "initial_state": self.initial_state,
            "transitions": {
                f"{state}|{symbol}": {
                    "next_state": transition.next_state,
                    "output_distribution": dict(
                        transition.output_distribution
                    ),
                    "next_state_distribution": dict(
                        transition.next_state_distribution or {}
                    ),
                }
                for (state, symbol), transition in sorted(
                    self.transitions.items()
                )
            },
        }
        return sha256(
            dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    def output_distribution(
        self,
        inputs: Sequence[str],
    ) -> dict[tuple[str, ...], float]:
        frontier: dict[tuple[str, tuple[str, ...]], float] = {
            (self.initial_state, ()): 1.0
        }
        for symbol in inputs:
            if symbol not in self.alphabet:
                raise KeyError(symbol)
            next_frontier: dict[
                tuple[str, tuple[str, ...]],
                float,
            ] = defaultdict(float)
            for (state, outputs), mass in frontier.items():
                transition = self.transitions[(state, symbol)]
                states = transition.next_state_distribution or {
                    transition.next_state: 1.0
                }
                for output, output_probability in (
                    transition.output_distribution.items()
                ):
                    for next_state, state_probability in states.items():
                        next_frontier[
                            (next_state, outputs + (output,))
                        ] += (
                            mass
                            * output_probability
                            * state_probability
                        )
            frontier = next_frontier
        result: dict[tuple[str, ...], float] = defaultdict(float)
        for (_, outputs), mass in frontier.items():
            result[outputs] += mass
        return dict(sorted(result.items()))

    def likelihood(
        self,
        observation: ProbabilisticObservation,
        *,
        floor: float = 1.0e-15,
    ) -> float:
        distribution = self.output_distribution(observation.inputs)
        return max(
            floor,
            distribution.get(observation.outputs, 0.0),
        ) ** observation.weight

    def log_likelihood(
        self,
        observations: Sequence[ProbabilisticObservation],
        *,
        floor: float = 1.0e-15,
    ) -> float:
        return sum(
            log(self.likelihood(observation, floor=floor))
            for observation in observations
        )

    def sample(
        self,
        inputs: Sequence[str],
        *,
        seed: int = 0,
    ) -> tuple[str, ...]:
        generator = Random(seed)
        state = self.initial_state
        outputs: list[str] = []

        def choose(distribution: Mapping[str, float]) -> str:
            threshold = generator.random()
            cumulative = 0.0
            for value, probability in distribution.items():
                cumulative += probability
                if threshold <= cumulative:
                    return value
            return next(reversed(distribution))

        for symbol in inputs:
            transition = self.transitions[(state, symbol)]
            outputs.append(choose(transition.output_distribution))
            if transition.next_state_distribution:
                state = choose(transition.next_state_distribution)
            else:
                state = transition.next_state
        return tuple(outputs)


def posterior(
    candidates: Sequence[ProbabilisticMealyMachine],
    observations: Sequence[ProbabilisticObservation],
    *,
    priors: Mapping[str, float] | None = None,
    complexity_penalty: float = 0.0,
) -> dict[str, float]:
    if not candidates:
        raise ValueError("candidates cannot be empty")
    raw: dict[str, float] = {}
    for candidate in candidates:
        prior = (
            priors.get(candidate.machine_id, 0.0)
            if priors
            else 1.0 / len(candidates)
        )
        if prior <= 0:
            raw[candidate.machine_id] = float("-inf")
            continue
        complexity = len(candidate.states) * len(candidate.alphabet)
        raw[candidate.machine_id] = (
            log(prior)
            + candidate.log_likelihood(observations)
            - complexity_penalty * complexity
        )
    peak = max(raw.values())
    weights = {
        key: (
            0.0
            if value == float("-inf")
            else exp(value - peak)
        )
        for key, value in raw.items()
    }
    return _normalise(weights)


def entropy_bits(distribution: Mapping[str, float]) -> float:
    normalised = _normalise(distribution)
    return -sum(
        value * log2(value)
        for value in normalised.values()
        if value > 0
    )


def predictive_distribution(
    candidates: Sequence[ProbabilisticMealyMachine],
    inputs: Sequence[str],
    candidate_posterior: Mapping[str, float],
) -> dict[tuple[str, ...], float]:
    total: dict[tuple[str, ...], float] = defaultdict(float)
    weights = _normalise(
        {
            candidate.machine_id: candidate_posterior.get(
                candidate.machine_id,
                0.0,
            )
            for candidate in candidates
        }
    )
    for candidate in candidates:
        for outputs, probability in candidate.output_distribution(
            inputs
        ).items():
            total[outputs] += (
                weights[candidate.machine_id] * probability
            )
    mass = sum(total.values())
    return {
        key: value / mass
        for key, value in sorted(total.items())
    }


def total_variation(
    left: Mapping[tuple[str, ...], float],
    right: Mapping[tuple[str, ...], float],
) -> float:
    keys = set(left) | set(right)
    return 0.5 * sum(
        abs(left.get(key, 0.0) - right.get(key, 0.0))
        for key in keys
    )


def behavioral_distance(
    left: ProbabilisticMealyMachine,
    right: ProbabilisticMealyMachine,
    experiments: Iterable[Sequence[str]],
) -> float:
    distances = [
        total_variation(
            left.output_distribution(experiment),
            right.output_distribution(experiment),
        )
        for experiment in experiments
    ]
    return max(distances, default=0.0)


def expected_information_gain(
    candidates: Sequence[ProbabilisticMealyMachine],
    inputs: Sequence[str],
    candidate_posterior: Mapping[str, float],
) -> float:
    prior_entropy = entropy_bits(candidate_posterior)
    outcome_distribution = predictive_distribution(
        candidates,
        inputs,
        candidate_posterior,
    )
    expected_remaining = 0.0
    for outputs, outcome_probability in outcome_distribution.items():
        updated_weights: dict[str, float] = {}
        for candidate in candidates:
            likelihood = candidate.output_distribution(inputs).get(
                outputs,
                0.0,
            )
            updated_weights[candidate.machine_id] = (
                candidate_posterior.get(candidate.machine_id, 0.0)
                * likelihood
            )
        if sum(updated_weights.values()) > 0:
            expected_remaining += (
                outcome_probability * entropy_bits(updated_weights)
            )
    return max(0.0, prior_entropy - expected_remaining)


def demo_probabilistic_pair() -> tuple[
    ProbabilisticMealyMachine,
    ProbabilisticMealyMachine,
]:
    states = ("S0", "S1")
    alphabet = ("A", "B")
    common = {
        ("S0", "A"): ProbabilisticTransition(
            "S1",
            {"0": 0.8, "1": 0.2},
        ),
        ("S0", "B"): ProbabilisticTransition(
            "S0",
            {"0": 0.5, "1": 0.5},
        ),
        ("S1", "A"): ProbabilisticTransition(
            "S1",
            {"1": 0.9, "0": 0.1},
        ),
    }
    left_transitions = dict(common)
    left_transitions[("S1", "B")] = ProbabilisticTransition(
        "S0",
        {"1": 0.75, "0": 0.25},
    )
    right_transitions = dict(common)
    right_transitions[("S1", "B")] = ProbabilisticTransition(
        "S0",
        {"1": 0.25, "0": 0.75},
    )
    return (
        ProbabilisticMealyMachine(
            "prob-left",
            states,
            alphabet,
            left_transitions,
            initial_state="S0",
        ),
        ProbabilisticMealyMachine(
            "prob-right",
            states,
            alphabet,
            right_transitions,
            initial_state="S0",
        ),
    )
