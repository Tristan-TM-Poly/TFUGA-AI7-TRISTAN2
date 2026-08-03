"""Finite-difference and Newton-series discovery."""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .exact import binomial_polynomial_value, fraction_text, vector_complexity


def difference_table(terms: Sequence[Fraction]) -> list[list[Fraction]]:
    """Return all forward-difference rows, beginning with the input row."""

    if not terms:
        raise ValueError("difference table requires at least one term")
    rows = [list(terms)]
    while len(rows[-1]) > 1:
        current = rows[-1]
        rows.append([current[index + 1] - current[index] for index in range(len(current) - 1)])
    return rows


def detect_newton_polynomial(
    terms: Sequence[Fraction],
    *,
    max_degree: int | None = None,
) -> tuple[list[Fraction], int] | None:
    """Detect the smallest polynomial degree supported non-trivially by data.

    A degree ``d`` candidate is accepted only when the ``d``-th difference row
    contains at least two equal values.  This rejects the vacuous degree
    ``len(terms)-1`` interpolant that every finite prefix possesses.
    """

    if len(terms) < 2:
        return None
    rows = difference_table(terms)
    ceiling = len(terms) - 2
    if max_degree is not None:
        ceiling = min(ceiling, max_degree)

    for degree in range(ceiling + 1):
        row = rows[degree]
        if len(row) >= 2 and all(value == row[0] for value in row[1:]):
            coefficients = [rows[index][0] for index in range(degree + 1)]
            return coefficients, degree
    return None


def evaluate_newton(coefficients: Sequence[Fraction], n: int) -> Fraction:
    return binomial_polynomial_value(coefficients, n)


def newton_expression(coefficients: Sequence[Fraction]) -> str:
    """Render an exact formula in the binomial basis."""

    pieces: list[str] = []
    for degree, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        basis = "1" if degree == 0 else ("n" if degree == 1 else f"binom(n,{degree})")
        if degree == 0:
            pieces.append(fraction_text(coefficient))
        elif coefficient == 1:
            pieces.append(basis)
        elif coefficient == -1:
            pieces.append(f"-{basis}")
        else:
            pieces.append(f"{fraction_text(coefficient)}*{basis}")
    if not pieces:
        return "a[n] = 0"
    expression = " + ".join(pieces).replace("+ -", "- ")
    return f"a[n] = {expression}"


def polynomial_complexity(coefficients: Sequence[Fraction]) -> int:
    return len(coefficients) + vector_complexity(coefficients)
