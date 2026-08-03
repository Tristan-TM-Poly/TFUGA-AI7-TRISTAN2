"""Exact linear-recurrence discovery and rational generating functions."""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .exact import fraction_text, solve_unique_linear_system, vector_complexity


def detect_linear_recurrence(
    terms: Sequence[Fraction],
    *,
    max_order: int | None = None,
) -> list[Fraction] | None:
    """Find the smallest exact constant-coefficient recurrence.

    The convention is ``a[n] = c[0] a[n-1] + ... + c[r-1] a[n-r]``.
    Orders that are underdetermined by the available prefix are rejected.
    """

    if len(terms) < 3:
        return None
    ceiling = (len(terms) - 1) // 2
    if max_order is not None:
        ceiling = min(ceiling, max_order)

    for order in range(1, ceiling + 1):
        matrix: list[list[Fraction]] = []
        rhs: list[Fraction] = []
        for n in range(order, len(terms)):
            matrix.append([terms[n - lag] for lag in range(1, order + 1)])
            rhs.append(terms[n])
        coefficients = solve_unique_linear_system(matrix, rhs)
        if coefficients is None:
            continue
        if verify_recurrence(terms, coefficients):
            return coefficients
    return None


def verify_recurrence(terms: Sequence[Fraction], coefficients: Sequence[Fraction]) -> bool:
    order = len(coefficients)
    if order == 0 or len(terms) <= order:
        return False
    return all(
        terms[n] == sum(
            (coefficients[lag - 1] * terms[n - lag] for lag in range(1, order + 1)),
            Fraction(0),
        )
        for n in range(order, len(terms))
    )


def recurrence_value(seed: Sequence[Fraction], coefficients: Sequence[Fraction], n: int) -> Fraction:
    """Evaluate a recurrence exactly from an initial seed."""

    if n < 0:
        raise ValueError("n must be non-negative")
    order = len(coefficients)
    if order == 0 or len(seed) < order:
        raise ValueError("seed must contain at least recurrence-order terms")
    values = list(seed[:order])
    if n < len(values):
        return values[n]
    while len(values) <= n:
        index = len(values)
        values.append(sum(
            (coefficients[lag - 1] * values[index - lag] for lag in range(1, order + 1)),
            Fraction(0),
        ))
    return values[n]


def recurrence_expression(coefficients: Sequence[Fraction]) -> str:
    pieces: list[str] = []
    for lag, coefficient in enumerate(coefficients, start=1):
        if coefficient == 0:
            continue
        term = f"a[n-{lag}]"
        if coefficient == 1:
            pieces.append(term)
        elif coefficient == -1:
            pieces.append(f"-{term}")
        else:
            pieces.append(f"{fraction_text(coefficient)}*{term}")
    rhs = " + ".join(pieces).replace("+ -", "- ") if pieces else "0"
    return f"a[n] = {rhs}"


def rational_generating_coefficients(
    seed: Sequence[Fraction],
    recurrence: Sequence[Fraction],
) -> tuple[list[Fraction], list[Fraction]]:
    """Compile a recurrence into ``A(z) = P(z) / Q(z)`` coefficients."""

    order = len(recurrence)
    if len(seed) < order:
        raise ValueError("seed must contain at least recurrence-order terms")
    denominator = [Fraction(1)] + [-coefficient for coefficient in recurrence]
    numerator: list[Fraction] = []
    for n in range(order):
        correction = sum(
            (recurrence[lag - 1] * seed[n - lag] for lag in range(1, min(n, order) + 1)),
            Fraction(0),
        )
        numerator.append(seed[n] - correction)
    while len(numerator) > 1 and numerator[-1] == 0:
        numerator.pop()
    return numerator, denominator


def rational_generating_expression(
    numerator: Sequence[Fraction],
    denominator: Sequence[Fraction],
) -> str:
    return f"A(z) = ({_polynomial_text(numerator)}) / ({_polynomial_text(denominator)})"


def recurrence_complexity(coefficients: Sequence[Fraction]) -> int:
    return 2 * len(coefficients) + vector_complexity(coefficients)


def _polynomial_text(coefficients: Sequence[Fraction]) -> str:
    pieces: list[str] = []
    for degree, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        variable = "" if degree == 0 else ("z" if degree == 1 else f"z^{degree}")
        magnitude = abs(coefficient)
        if degree == 0:
            body = fraction_text(magnitude)
        elif magnitude == 1:
            body = variable
        else:
            body = f"{fraction_text(magnitude)}*{variable}"
        if not pieces:
            pieces.append(body if coefficient > 0 else f"-{body}")
        else:
            pieces.append((" + " if coefficient > 0 else " - ") + body)
    return "".join(pieces) if pieces else "0"
