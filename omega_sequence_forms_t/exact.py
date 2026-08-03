"""Exact arithmetic helpers for Ω-SUITE-FORM-T∞."""
from __future__ import annotations

from fractions import Fraction
from math import comb
from typing import Iterable, Sequence


NumberLike = int | float | str | Fraction


def as_fraction(value: NumberLike, *, max_denominator: int = 1_000_000) -> Fraction:
    """Convert supported inputs to deterministic rational values.

    Floats are deliberately reconstructed with a bounded denominator.  Exact
    scientific work should pass integers, strings or ``Fraction`` objects.
    """

    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        return Fraction(int(value), 1)
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value.strip())
    if isinstance(value, float):
        return Fraction(value).limit_denominator(max_denominator)
    raise TypeError(f"unsupported sequence value: {type(value)!r}")


def normalize_terms(values: Iterable[NumberLike]) -> tuple[Fraction, ...]:
    terms = tuple(as_fraction(value) for value in values)
    if not terms:
        raise ValueError("at least one sequence term is required")
    return terms


def solve_unique_linear_system(
    matrix: Sequence[Sequence[Fraction]],
    rhs: Sequence[Fraction],
) -> list[Fraction] | None:
    """Solve an overdetermined rational system when it has a unique solution.

    Returns ``None`` for inconsistent or underdetermined systems.  The routine
    uses exact Gauss-Jordan elimination and is intentionally dependency-free.
    """

    if len(matrix) != len(rhs):
        raise ValueError("matrix and right-hand side lengths differ")
    if not matrix:
        return None
    width = len(matrix[0])
    if width == 0 or any(len(row) != width for row in matrix):
        raise ValueError("matrix must be non-empty and rectangular")

    augmented = [list(row) + [rhs_value] for row, rhs_value in zip(matrix, rhs)]
    pivot_rows: dict[int, int] = {}
    row_index = 0

    for column in range(width):
        pivot = next(
            (candidate for candidate in range(row_index, len(augmented)) if augmented[candidate][column]),
            None,
        )
        if pivot is None:
            continue
        augmented[row_index], augmented[pivot] = augmented[pivot], augmented[row_index]
        divisor = augmented[row_index][column]
        augmented[row_index] = [value / divisor for value in augmented[row_index]]

        for other in range(len(augmented)):
            if other == row_index:
                continue
            factor = augmented[other][column]
            if factor:
                augmented[other] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(augmented[other], augmented[row_index])
                ]

        pivot_rows[column] = row_index
        row_index += 1
        if row_index == len(augmented):
            break

    for row in augmented:
        if all(value == 0 for value in row[:width]) and row[width] != 0:
            return None
    if len(pivot_rows) != width:
        return None

    solution = [Fraction(0) for _ in range(width)]
    for column, pivot_row in pivot_rows.items():
        solution[column] = augmented[pivot_row][width]
    return solution


def binomial_polynomial_value(coefficients: Sequence[Fraction], n: int) -> Fraction:
    """Evaluate ``sum_k coefficients[k] * binom(n, k)`` exactly."""

    if n < 0:
        raise ValueError("n must be non-negative")
    return sum((coefficient * comb(n, k) for k, coefficient in enumerate(coefficients)), Fraction(0))


def fraction_complexity(value: Fraction) -> int:
    """Small deterministic description-length proxy."""

    return max(1, abs(value.numerator).bit_length()) + max(1, value.denominator.bit_length())


def vector_complexity(values: Sequence[Fraction]) -> int:
    return sum(fraction_complexity(value) for value in values)


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"({value.numerator}/{value.denominator})"
