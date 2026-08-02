"""Bounded probabilistic transducers for authorized synthetic reverse engineering.

The module models observable behavior only. A high likelihood or low divergence
is evidence of behavioral compatibility on a declared query set, not proof of
internal identity.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Hashable, Iterable, Mapping, MutableMapping, Sequence

State = Hashable
Symbol = Hashable
Output = Hashable


@dataclass(frozen=True, order=True)
class Outcome:
    next_state: State
    output: Output


def normalize(weights: Mapping[Outcome, float]) -> dict[Outcome, float]:
    if not weights:
        raise ValueError("distribution must contain at least one outcome")
    checked: dict[Outcome, float] = {}
    total = 0.0
    for outcome, weight in weights.items():
        value = float(weight)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("weights must be finite and non-negative")
        checked[outcome] = value
        total += value
    if total <= 0.0:
        raise ValueError("distribution total must be positive")
    return {outcome: weight / total for outcome, weight in checked.items()}


def entropy_bits(probabilities: Iterable[float]) -> float:
    entropy = 0.0
    for probability in probabilities:
        p = float(probability)
        if p < 0.0 or p > 1.0 or not math.isfinite(p):
            raise ValueError("probabilities must be finite and within [0, 1]")
        if p:
            entropy -= p * math.log2(p)
    return entropy


def total_variation(left: Mapping[Outcome, float], right: Mapping[Outcome, float]) -> float:
    support = set(left) | set(right)
    return 0.5 * sum(abs(left.get(item, 0.0) - right.get(item, 0.0)) for item in support)


class ProbabilisticTransducer:
    """Finite stochastic Mealy-like model with explicit outcome distributions."""

    def __init__(
        self,
        *,
        initial_state: State,
        transitions: Mapping[tuple[State, Symbol], Mapping[Outcome, float]],
    ) -> None:
        if not transitions:
            raise ValueError("transitions cannot be empty")
        self.initial_state = initial_state
        self._transitions = {key: normalize(value) for key, value in transitions.items()}

    def distribution(self, state: State, symbol: Symbol) -> dict[Outcome, float]:
        try:
            return dict(self._transitions[(state, symbol)])
        except KeyError as exc:
            raise KeyError(f"undefined transition for state={state!r}, symbol={symbol!r}") from exc

    def sample_step(self, state: State, symbol: Symbol, rng: random.Random) -> Outcome:
        distribution = self.distribution(state, symbol)
        threshold = rng.random()
        cumulative = 0.0
        ordered = sorted(distribution.items(), key=lambda pair: repr(pair[0]))
        for outcome, probability in ordered:
            cumulative += probability
            if threshold <= cumulative:
                return outcome
        return ordered[-1][0]

    def sample_trace(self, symbols: Sequence[Symbol], *, seed: int = 0) -> tuple[Output, ...]:
        rng = random.Random(seed)
        state = self.initial_state
        outputs: list[Output] = []
        for symbol in symbols:
            outcome = self.sample_step(state, symbol, rng)
            state = outcome.next_state
            outputs.append(outcome.output)
        return tuple(outputs)

    def trace_probability(self, symbols: Sequence[Symbol], outputs: Sequence[Output]) -> float:
        if len(symbols) != len(outputs):
            raise ValueError("symbols and outputs must have equal length")
        state_mass: dict[State, float] = {self.initial_state: 1.0}
        for symbol, observed_output in zip(symbols, outputs, strict=True):
            next_mass: MutableMapping[State, float] = {}
            for state, state_probability in state_mass.items():
                for outcome, probability in self.distribution(state, symbol).items():
                    if outcome.output == observed_output:
                        next_mass[outcome.next_state] = (
                            next_mass.get(outcome.next_state, 0.0) + state_probability * probability
                        )
            state_mass = dict(next_mass)
            if not state_mass:
                return 0.0
        return sum(state_mass.values())

    def trace_log_likelihood(self, symbols: Sequence[Symbol], outputs: Sequence[Output]) -> float:
        probability = self.trace_probability(symbols, outputs)
        return -math.inf if probability == 0.0 else math.log(probability)

    def query_divergence(
        self,
        other: "ProbabilisticTransducer",
        queries: Iterable[tuple[State, Symbol]],
    ) -> dict[str, float]:
        distances = [
            total_variation(self.distribution(state, symbol), other.distribution(state, symbol))
            for state, symbol in queries
        ]
        if not distances:
            raise ValueError("queries cannot be empty")
        return {
            "mean_total_variation": sum(distances) / len(distances),
            "max_total_variation": max(distances),
            "query_count": float(len(distances)),
        }


class DirichletTransitionEstimator:
    """Small conjugate estimator that keeps support and uncertainty explicit."""

    def __init__(self, support: Mapping[tuple[State, Symbol], Iterable[Outcome]], *, alpha: float = 1.0) -> None:
        if not math.isfinite(alpha) or alpha <= 0.0:
            raise ValueError("alpha must be finite and positive")
        self.alpha = float(alpha)
        self._support = {key: tuple(dict.fromkeys(outcomes)) for key, outcomes in support.items()}
        if any(not outcomes for outcomes in self._support.values()):
            raise ValueError("every transition support must be non-empty")
        self._counts: dict[tuple[State, Symbol], dict[Outcome, int]] = {
            key: {outcome: 0 for outcome in outcomes} for key, outcomes in self._support.items()
        }

    def observe(self, state: State, symbol: Symbol, outcome: Outcome) -> None:
        key = (state, symbol)
        if key not in self._counts or outcome not in self._counts[key]:
            raise ValueError("observation lies outside declared support")
        self._counts[key][outcome] += 1

    def posterior_distribution(self, state: State, symbol: Symbol) -> dict[Outcome, float]:
        key = (state, symbol)
        counts = self._counts[key]
        total = sum(counts.values()) + self.alpha * len(counts)
        return {outcome: (count + self.alpha) / total for outcome, count in counts.items()}

    def posterior_entropy(self, state: State, symbol: Symbol) -> float:
        return entropy_bits(self.posterior_distribution(state, symbol).values())

    def to_model(self, *, initial_state: State) -> ProbabilisticTransducer:
        transitions = {key: self.posterior_distribution(*key) for key in self._support}
        return ProbabilisticTransducer(initial_state=initial_state, transitions=transitions)
