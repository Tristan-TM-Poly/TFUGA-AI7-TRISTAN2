"""Exact rational-function discovery for a_n=P(n)/Q(n)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import Iterable, Sequence

from ..exact import NumberLike, normalize_terms, solve_unique_linear_system, vector_complexity


@dataclass(frozen=True)
class RationalIndexCandidate:
    numerator: tuple[Fraction, ...]
    denominator: tuple[Fraction, ...]
    numerator_degree: int
    denominator_degree: int
    fitted_terms: int
    fitted_matches: int
    held_out_terms: int
    held_out_matches: int
    singular_indices: tuple[int, ...]

    def evaluate(self, n: int) -> Fraction:
        if n < 0:
            raise ValueError("n must be non-negative")
        numerator = _poly_eval(self.numerator, n)
        denominator = _poly_eval(self.denominator, n)
        if denominator == 0:
            raise ZeroDivisionError(f"candidate denominator vanishes at n={n}")
        return numerator / denominator

    @property
    def predicts_holdout(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches

    @property
    def complexity(self) -> int:
        return vector_complexity(self.numerator) + vector_complexity(self.denominator)

    def expression(self) -> str:
        return f"({_poly_text(self.numerator)})/({_poly_text(self.denominator)})"

    def to_dict(self) -> dict[str, object]:
        return {
            "family": "rational_index",
            "expression": self.expression(),
            "numerator": [str(value) for value in self.numerator],
            "denominator": [str(value) for value in self.denominator],
            "numerator_degree": self.numerator_degree,
            "denominator_degree": self.denominator_degree,
            "singular_indices": list(self.singular_indices),
            "complexity": self.complexity,
            "validation": {
                "fitted_terms": self.fitted_terms,
                "fitted_matches": self.fitted_matches,
                "held_out_terms": self.held_out_terms,
                "held_out_matches": self.held_out_matches,
            },
            "global_identity_proved": False,
        }


def _poly_eval(coefficients: Sequence[Fraction], n: int | Fraction) -> Fraction:
    result = Fraction(0)
    x = Fraction(n)
    for coefficient in reversed(coefficients):
        result = result * x + coefficient
    return result


def _trim(coefficients: Sequence[Fraction]) -> tuple[Fraction, ...]:
    values = list(coefficients)
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return tuple(values)


def _poly_text(coefficients: Sequence[Fraction]) -> str:
    terms = []
    for degree, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        if degree == 0:
            term = f"{coefficient}"
        elif degree == 1:
            term = f"({coefficient})*n"
        else:
            term = f"({coefficient})*n^{degree}"
        terms.append(term)
    return " + ".join(terms) if terms else "0"


def _default_holdout(term_count: int) -> int:
    if term_count < 8:
        return 0
    return max(2, min(16, term_count // 4))


def fit_rational_index(
    terms: Iterable[NumberLike],
    *,
    numerator_degree: int,
    denominator_degree: int,
    holdout: int | None = None,
) -> RationalIndexCandidate | None:
    values = normalize_terms(terms)
    if numerator_degree < 0 or denominator_degree < 0:
        raise ValueError("degrees must be non-negative")
    if holdout is None:
        holdout = _default_holdout(len(values))
    if not 0 <= holdout < len(values):
        raise ValueError("invalid holdout")
    training_count = len(values) - holdout
    unknowns = numerator_degree + 1 + denominator_degree
    if training_count <= unknowns:
        return None

    # Normalize Q(0)=1: Q(n)=1+sum_{j=1}^d q_j n^j.
    matrix: list[list[Fraction]] = []
    rhs: list[Fraction] = []
    for n, value in enumerate(values[:training_count]):
        row = [Fraction(n) ** degree for degree in range(numerator_degree + 1)]
        row.extend(-(value * (Fraction(n) ** degree)) for degree in range(1, denominator_degree + 1))
        matrix.append(row)
        rhs.append(value)
    solution = solve_unique_linear_system(matrix, rhs)
    if solution is None:
        return None

    numerator = _trim(solution[: numerator_degree + 1])
    denominator = _trim((Fraction(1), *solution[numerator_degree + 1 :]))
    singular = tuple(index for index in range(len(values)) if _poly_eval(denominator, index) == 0)
    if singular:
        return None

    def evaluate(index: int) -> Fraction:
        return _poly_eval(numerator, index) / _poly_eval(denominator, index)

    fitted_matches = sum(evaluate(index) == values[index] for index in range(training_count))
    held_matches = sum(evaluate(index) == values[index] for index in range(training_count, len(values)))
    if fitted_matches != training_count:
        return None
    return RationalIndexCandidate(
        numerator=numerator,
        denominator=denominator,
        numerator_degree=len(numerator) - 1,
        denominator_degree=len(denominator) - 1,
        fitted_terms=training_count,
        fitted_matches=fitted_matches,
        held_out_terms=holdout,
        held_out_matches=held_matches,
        singular_indices=singular,
    )


def discover_rational_indices(
    terms: Iterable[NumberLike],
    *,
    max_numerator_degree: int = 8,
    max_denominator_degree: int = 8,
    holdout: int | None = None,
) -> tuple[RationalIndexCandidate, ...]:
    values = normalize_terms(terms)
    candidates: list[RationalIndexCandidate] = []
    for total_degree in range(max_numerator_degree + max_denominator_degree + 1):
        for denominator_degree in range(min(max_denominator_degree, total_degree) + 1):
            numerator_degree = total_degree - denominator_degree
            if numerator_degree > max_numerator_degree:
                continue
            candidate = fit_rational_index(
                values,
                numerator_degree=numerator_degree,
                denominator_degree=denominator_degree,
                holdout=holdout,
            )
            if candidate is not None:
                candidates.append(candidate)
    unique: dict[tuple[tuple[Fraction, ...], tuple[Fraction, ...]], RationalIndexCandidate] = {}
    for candidate in candidates:
        unique[(candidate.numerator, candidate.denominator)] = candidate
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            not item.predicts_holdout,
            item.numerator_degree + item.denominator_degree,
            item.complexity,
        ),
    )
    return tuple(ordered)


def rational_fixture(
    numerator: Sequence[int],
    denominator: Sequence[int],
    count: int,
) -> tuple[Fraction, ...]:
    p = tuple(Fraction(value) for value in numerator)
    q = tuple(Fraction(value) for value in denominator)
    result = []
    for n in range(count):
        qn = _poly_eval(q, n)
        if qn == 0:
            raise ZeroDivisionError(f"fixture denominator vanishes at n={n}")
        result.append(_poly_eval(p, n) / qn)
    return tuple(result)
