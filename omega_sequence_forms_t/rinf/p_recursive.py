"""Exact guessing of polynomial-coefficient linear recurrences.

The detector searches operators

    L = sum_{j=0}^r p_j(n) E^j

with deg p_j <= d.  Because the coefficient system is homogeneous, one
coefficient is normalized to one and the remaining overdetermined rational
system is solved exactly.  Every candidate is substituted back into all
available equations.  This is a conjecture generator, not a proof that the
operator annihilates terms beyond the finite prefix.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Iterator, Sequence

from ..exact import NumberLike, normalize_terms, solve_unique_linear_system, vector_complexity


@dataclass(frozen=True)
class PRecursiveOperator:
    order: int
    degree: int
    coefficients: tuple[tuple[Fraction, ...], ...]
    normalized_pivot: tuple[int, int]

    def __post_init__(self) -> None:
        if self.order < 1 or self.degree < 0:
            raise ValueError("invalid operator dimensions")
        if len(self.coefficients) != self.order + 1:
            raise ValueError("operator block count mismatch")
        if any(len(block) != self.degree + 1 for block in self.coefficients):
            raise ValueError("operator polynomial degree mismatch")

    def polynomial(self, shift: int, n: int) -> Fraction:
        result = Fraction(0)
        for coefficient in reversed(self.coefficients[shift]):
            result = result * n + coefficient
        return result

    def apply(self, terms: Sequence[Fraction], n: int) -> Fraction:
        if n < 0 or n + self.order >= len(terms):
            raise IndexError("operator application outside supplied terms")
        return sum(
            (self.polynomial(shift, n) * terms[n + shift] for shift in range(self.order + 1)),
            Fraction(0),
        )

    @property
    def complexity(self) -> int:
        return self.order + self.degree + sum(vector_complexity(block) for block in self.coefficients)

    def expression(self) -> str:
        blocks = []
        for shift, block in enumerate(self.coefficients):
            polynomial_terms = []
            for degree, coefficient in enumerate(block):
                if coefficient == 0:
                    continue
                if degree == 0:
                    term = f"{coefficient}"
                elif degree == 1:
                    term = f"({coefficient})*n"
                else:
                    term = f"({coefficient})*n^{degree}"
                polynomial_terms.append(term)
            polynomial = " + ".join(polynomial_terms) if polynomial_terms else "0"
            blocks.append(f"({polynomial})*a[n+{shift}]")
        return " + ".join(blocks) + " = 0"

    def to_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "degree": self.degree,
            "coefficients": [[str(value) for value in block] for block in self.coefficients],
            "normalized_pivot": list(self.normalized_pivot),
            "complexity": self.complexity,
            "expression": self.expression(),
        }


@dataclass(frozen=True)
class PRecursiveCandidate:
    operator: PRecursiveOperator
    fitted_equations: int
    fitted_matches: int
    held_out_equations: int
    held_out_matches: int
    training_terms: int
    total_terms: int

    @property
    def exact_fit(self) -> bool:
        return self.fitted_equations > 0 and self.fitted_equations == self.fitted_matches

    @property
    def predicts_holdout(self) -> bool:
        return self.held_out_equations > 0 and self.held_out_equations == self.held_out_matches

    def to_dict(self) -> dict[str, object]:
        return {
            "family": "p_recursive",
            "operator": self.operator.to_dict(),
            "validation": {
                "fitted_equations": self.fitted_equations,
                "fitted_matches": self.fitted_matches,
                "held_out_equations": self.held_out_equations,
                "held_out_matches": self.held_out_matches,
            },
            "training_terms": self.training_terms,
            "total_terms": self.total_terms,
            "global_identity_proved": False,
        }


def _column_index(shift: int, degree: int, max_degree: int) -> int:
    return shift * (max_degree + 1) + degree


def _decode_coefficients(
    values: Sequence[Fraction],
    *,
    order: int,
    degree: int,
) -> tuple[tuple[Fraction, ...], ...]:
    width = degree + 1
    return tuple(tuple(values[start : start + width]) for start in range(0, len(values), width))


def _equation_row(terms: Sequence[Fraction], n: int, order: int, degree: int) -> list[Fraction]:
    row: list[Fraction] = []
    for shift in range(order + 1):
        value = terms[n + shift]
        row.extend(value * Fraction(n) ** power for power in range(degree + 1))
    return row


def _normalize_global(coefficients: Sequence[Fraction]) -> tuple[Fraction, ...]:
    first = next((value for value in coefficients if value), None)
    if first is None:
        raise ValueError("zero operator")
    normalized = tuple(value / first for value in coefficients)
    if next(value for value in normalized if value) < 0:
        normalized = tuple(-value for value in normalized)
    return normalized


def _candidate_from_pivot(
    rows: Sequence[Sequence[Fraction]],
    *,
    pivot: int,
    order: int,
    degree: int,
) -> PRecursiveOperator | None:
    width = len(rows[0])
    matrix = []
    rhs = []
    for row in rows:
        matrix.append([row[column] for column in range(width) if column != pivot])
        rhs.append(-row[pivot])
    solution = solve_unique_linear_system(matrix, rhs)
    if solution is None:
        return None
    full = list(solution)
    full.insert(pivot, Fraction(1))
    normalized = _normalize_global(full)
    coefficients = _decode_coefficients(normalized, order=order, degree=degree)
    pivot_shift, pivot_degree = divmod(pivot, degree + 1)
    return PRecursiveOperator(order, degree, coefficients, (pivot_shift, pivot_degree))


def fit_p_recursive(
    terms: Iterable[NumberLike],
    *,
    order: int,
    degree: int,
    holdout_equations: int = 0,
) -> tuple[PRecursiveCandidate, ...]:
    values = normalize_terms(terms)
    if order < 1 or degree < 0:
        raise ValueError("order must be >=1 and degree >=0")
    equation_count = len(values) - order
    if equation_count <= 0:
        return ()
    if not 0 <= holdout_equations < equation_count:
        raise ValueError("invalid holdout equation count")
    training_equations = equation_count - holdout_equations
    unknown_count = (order + 1) * (degree + 1)
    # Normalizing one coefficient leaves unknown_count-1 variables.  Require
    # at least one extra equation to reject exact memorization.
    if training_equations <= unknown_count - 1:
        return ()

    rows = [_equation_row(values, n, order, degree) for n in range(equation_count)]
    training_rows = rows[:training_equations]
    found: dict[tuple[tuple[Fraction, ...], ...], PRecursiveCandidate] = {}
    for pivot in range(unknown_count):
        operator = _candidate_from_pivot(
            training_rows,
            pivot=pivot,
            order=order,
            degree=degree,
        )
        if operator is None:
            continue
        key = operator.coefficients
        fitted_matches = sum(operator.apply(values, n) == 0 for n in range(training_equations))
        held_matches = sum(operator.apply(values, n) == 0 for n in range(training_equations, equation_count))
        if fitted_matches != training_equations:
            continue
        found[key] = PRecursiveCandidate(
            operator=operator,
            fitted_equations=training_equations,
            fitted_matches=fitted_matches,
            held_out_equations=holdout_equations,
            held_out_matches=held_matches,
            training_terms=training_equations + order,
            total_terms=len(values),
        )
    return tuple(sorted(found.values(), key=lambda item: item.operator.complexity))


def discover_p_recursive(
    terms: Iterable[NumberLike],
    *,
    max_order: int = 8,
    max_degree: int = 8,
    holdout_equations: int | None = None,
) -> tuple[PRecursiveCandidate, ...]:
    values = normalize_terms(terms)
    if holdout_equations is None:
        holdout_equations = 0 if len(values) < 12 else max(2, min(16, len(values) // 5))
    candidates: list[PRecursiveCandidate] = []
    for complexity_shell in range(1, max_order + max_degree + 1):
        for order in range(1, min(max_order, complexity_shell) + 1):
            degree = complexity_shell - order
            if degree < 0 or degree > max_degree:
                continue
            candidates.extend(
                fit_p_recursive(
                    values,
                    order=order,
                    degree=degree,
                    holdout_equations=min(holdout_equations, max(0, len(values) - order - 1)),
                )
            )
    unique: dict[tuple[tuple[Fraction, ...], ...], PRecursiveCandidate] = {}
    for candidate in candidates:
        unique[candidate.operator.coefficients] = candidate
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            not item.predicts_holdout,
            item.operator.order + item.operator.degree,
            item.operator.complexity,
        ),
    )
    return tuple(ordered)


def verify_operator(operator: PRecursiveOperator, terms: Iterable[NumberLike]) -> tuple[int, int]:
    values = normalize_terms(terms)
    equation_count = max(0, len(values) - operator.order)
    matches = sum(operator.apply(values, n) == 0 for n in range(equation_count))
    return matches, equation_count


def factorial_fixture(count: int) -> tuple[Fraction, ...]:
    values = [Fraction(1)]
    for n in range(1, count):
        values.append(values[-1] * n)
    return tuple(values)
