"""Exact hypergeometric-ratio discovery and product-form compilation."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import prod
from typing import Iterable, Sequence

from ..exact import NumberLike, normalize_terms
from .rational_index import RationalIndexCandidate, discover_rational_indices


@dataclass(frozen=True)
class HypergeometricCandidate:
    initial_index: int
    initial_value: Fraction
    ratio: RationalIndexCandidate
    zero_indices: tuple[int, ...]
    fitted_terms: int
    fitted_matches: int
    held_out_terms: int
    held_out_matches: int

    def ratio_at(self, n: int) -> Fraction:
        return self.ratio.evaluate(n)

    def evaluate(self, n: int) -> Fraction:
        if n < self.initial_index:
            raise ValueError("evaluation before initial index is not supported")
        value = self.initial_value
        for index in range(self.initial_index, n):
            value *= self.ratio_at(index)
        return value

    @property
    def predicts_holdout(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches

    @property
    def complexity(self) -> int:
        return self.ratio.complexity + 2 + len(self.zero_indices)

    def expression(self) -> str:
        return (
            f"a_n=({self.initial_value})*Prod(k={self.initial_index}..n-1,"
            f"{self.ratio.expression().replace('n', 'k')})"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "family": "hypergeometric",
            "expression": self.expression(),
            "initial_index": self.initial_index,
            "initial_value": str(self.initial_value),
            "ratio": self.ratio.to_dict(),
            "zero_indices": list(self.zero_indices),
            "complexity": self.complexity,
            "validation": {
                "fitted_terms": self.fitted_terms,
                "fitted_matches": self.fitted_matches,
                "held_out_terms": self.held_out_terms,
                "held_out_matches": self.held_out_matches,
            },
            "global_identity_proved": False,
        }


def _default_holdout(term_count: int) -> int:
    if term_count < 10:
        return 0
    return max(2, min(16, term_count // 4))


def discover_hypergeometric(
    terms: Iterable[NumberLike],
    *,
    max_numerator_degree: int = 6,
    max_denominator_degree: int = 6,
    holdout: int | None = None,
) -> tuple[HypergeometricCandidate, ...]:
    values = normalize_terms(terms)
    if len(values) < 4:
        return ()
    if holdout is None:
        holdout = _default_holdout(len(values))
    if not 0 <= holdout < len(values) - 1:
        raise ValueError("holdout must leave at least two training terms")
    training_count = len(values) - holdout

    zero_indices = tuple(index for index, value in enumerate(values) if value == 0)
    if zero_indices:
        # R0∞ exact ratio detector deliberately refuses zero crossings rather
        # than silently divide by zero.  A future segmented detector can split
        # the sequence and carry explicit zero multiplicities.
        return ()

    ratios = tuple(values[index + 1] / values[index] for index in range(len(values) - 1))
    ratio_holdout = min(holdout, max(0, len(ratios) - 2))
    ratio_candidates = discover_rational_indices(
        ratios,
        max_numerator_degree=max_numerator_degree,
        max_denominator_degree=max_denominator_degree,
        holdout=ratio_holdout,
    )
    candidates: list[HypergeometricCandidate] = []
    for ratio in ratio_candidates:
        def evaluate(n: int) -> Fraction:
            value = values[0]
            for index in range(n):
                value *= ratio.evaluate(index)
            return value

        fitted_matches = sum(evaluate(index) == values[index] for index in range(training_count))
        held_matches = sum(evaluate(index) == values[index] for index in range(training_count, len(values)))
        if fitted_matches != training_count:
            continue
        candidates.append(
            HypergeometricCandidate(
                initial_index=0,
                initial_value=values[0],
                ratio=ratio,
                zero_indices=(),
                fitted_terms=training_count,
                fitted_matches=fitted_matches,
                held_out_terms=holdout,
                held_out_matches=held_matches,
            )
        )
    candidates.sort(key=lambda item: (not item.predicts_holdout, item.complexity))
    return tuple(candidates)


def factorial_fixture(count: int) -> tuple[Fraction, ...]:
    if count <= 0:
        raise ValueError("count must be positive")
    values = [Fraction(1)]
    for n in range(1, count):
        values.append(values[-1] * n)
    return tuple(values)


def central_binomial_fixture(count: int) -> tuple[Fraction, ...]:
    if count <= 0:
        raise ValueError("count must be positive")
    values = [Fraction(1)]
    for n in range(count - 1):
        values.append(values[-1] * Fraction(2 * (2 * n + 1), n + 1))
    return tuple(values)
