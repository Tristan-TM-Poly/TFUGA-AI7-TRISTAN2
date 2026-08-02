"""Probabilistic bounded CNF grammar with inside and Viterbi evidence.

Probabilities quantify one declared grammar.  They do not establish that the
same grammar or probabilities exist inside an inaccessible parser.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Mapping, Sequence


def _normalise(values: Mapping[object, float]) -> dict[object, float]:
    if not values:
        raise ValueError("rule distribution cannot be empty")
    checked: dict[object, float] = {}
    total = 0.0
    for key, value in values.items():
        probability = float(value)
        if not math.isfinite(probability) or probability < 0.0:
            raise ValueError("rule weights must be finite and non-negative")
        checked[key] = probability
        total += probability
    if total <= 0.0:
        raise ValueError("rule distribution must contain positive mass")
    return {key: value / total for key, value in checked.items()}


@dataclass(frozen=True)
class ProbabilisticParse:
    accepted: bool
    probability: float
    log_probability: float
    viterbi_probability: float
    viterbi_witness: tuple[str, ...]
    token_count: int
    claim: str = "bounded_probabilistic_cfg_only"


class ProbabilisticCFG:
    def __init__(
        self,
        *,
        start: str,
        terminal_rules: Mapping[str, Mapping[str, float]],
        binary_rules: Mapping[str, Mapping[tuple[str, str], float]],
    ) -> None:
        self.start = start
        self.terminal_rules = {
            lhs: _normalise(weights) for lhs, weights in terminal_rules.items()
        }
        self.binary_rules = {
            lhs: _normalise(weights) for lhs, weights in binary_rules.items()
        }
        if start not in set(self.terminal_rules) | set(self.binary_rules):
            raise ValueError("start symbol must have a rule")
        self._terminal_index: dict[str, list[tuple[str, float]]] = {}
        self._binary_index: dict[tuple[str, str], list[tuple[str, float]]] = {}
        for lhs, distribution in self.terminal_rules.items():
            for token, probability in distribution.items():
                self._terminal_index.setdefault(str(token), []).append((lhs, probability))
        for lhs, distribution in self.binary_rules.items():
            for pair, probability in distribution.items():
                self._binary_index.setdefault(pair, []).append((lhs, probability))

    def inside(self, tokens: Sequence[str], *, max_tokens: int = 64) -> ProbabilisticParse:
        sequence = tuple(map(str, tokens))
        if not sequence:
            return ProbabilisticParse(False, 0.0, -math.inf, 0.0, (), 0)
        if len(sequence) > max_tokens:
            raise ValueError("token budget exceeded")
        n = len(sequence)
        inside: list[list[dict[str, float]]] = [[{} for _ in range(n)] for _ in range(n)]
        viterbi: list[list[dict[str, tuple[float, tuple[str, ...]]]]] = [
            [{} for _ in range(n)] for _ in range(n)
        ]
        for index, token in enumerate(sequence):
            for lhs, probability in self._terminal_index.get(token, ()):
                inside[index][index][lhs] = inside[index][index].get(lhs, 0.0) + probability
                previous = viterbi[index][index].get(lhs, (0.0, ()))
                witness = (f"{lhs}->{token}",)
                if probability > previous[0]:
                    viterbi[index][index][lhs] = (probability, witness)
        for span in range(2, n + 1):
            for start in range(n - span + 1):
                end = start + span - 1
                for split in range(start, end):
                    for left_symbol, left_mass in inside[start][split].items():
                        for right_symbol, right_mass in inside[split + 1][end].items():
                            for parent, rule_probability in self._binary_index.get((left_symbol, right_symbol), ()):
                                contribution = rule_probability * left_mass * right_mass
                                inside[start][end][parent] = inside[start][end].get(parent, 0.0) + contribution
                                left_best = viterbi[start][split][left_symbol]
                                right_best = viterbi[split + 1][end][right_symbol]
                                score = rule_probability * left_best[0] * right_best[0]
                                previous = viterbi[start][end].get(parent, (0.0, ()))
                                if score > previous[0]:
                                    witness = (
                                        f"{parent}->{left_symbol} {right_symbol}@{split}",
                                    ) + left_best[1] + right_best[1]
                                    viterbi[start][end][parent] = (score, witness)
        probability = inside[0][n - 1].get(self.start, 0.0)
        best_probability, witness = viterbi[0][n - 1].get(self.start, (0.0, ()))
        return ProbabilisticParse(
            accepted=probability > 0.0,
            probability=probability,
            log_probability=-math.inf if probability <= 0.0 else math.log(probability),
            viterbi_probability=best_probability,
            viterbi_witness=witness,
            token_count=n,
        )

    def sample(self, *, seed: int, max_tokens: int = 16, max_expansions: int = 64) -> tuple[str, ...]:
        rng = random.Random(seed)
        frontier = [self.start]
        terminals: list[str] = []
        expansions = 0

        def choose(distribution: Mapping[object, float]):
            threshold = rng.random()
            cumulative = 0.0
            for key, probability in sorted(distribution.items(), key=lambda item: repr(item[0])):
                cumulative += probability
                if threshold <= cumulative:
                    return key
            return next(reversed(sorted(distribution, key=repr)))

        while frontier:
            expansions += 1
            if expansions > max_expansions:
                raise RuntimeError("expansion budget exceeded")
            symbol = frontier.pop()
            terminal_distribution = self.terminal_rules.get(symbol)
            binary_distribution = self.binary_rules.get(symbol)
            choices: dict[tuple[str, object], float] = {}
            if terminal_distribution:
                choices.update({("terminal", token): probability for token, probability in terminal_distribution.items()})
            if binary_distribution:
                choices.update({("binary", pair): probability for pair, probability in binary_distribution.items()})
            if not choices:
                raise KeyError(f"no rule for {symbol}")
            kind, value = choose(_normalise(choices))
            if kind == "terminal":
                terminals.append(str(value))
                if len(terminals) > max_tokens:
                    raise RuntimeError("token budget exceeded")
            else:
                left, right = value
                frontier.extend((right, left))
        return tuple(terminals)
