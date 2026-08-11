"""Exact rational algebra for Ω-ROOTFLOW-T∞ R0.6.

This module deliberately accepts integers/Fractions/rational strings and rejects
binary floating-point inputs. It is intended for exact OAK fixtures, not as a
symbolic computer algebra system.

Implemented exactly over ``fractions.Fraction``:

* polynomial derivative, division and monic gcd;
* Sylvester determinant and resultant;
* polynomial discriminant;
* Newton power sums;
* square-free / repeated-factor audit.

All coefficient vectors use ascending order ``[a0,...,an]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence


ExactScalar = int | Fraction | str
ExactPolynomial = tuple[Fraction, ...]


def _fraction(value: ExactScalar) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        return Fraction(int(value), 1)
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty rational token")
        return Fraction(text)
    raise TypeError(
        "exact rational APIs accept only int, Fraction, or rational string; "
        "binary floats are intentionally rejected"
    )


def _coerce_polynomial(values: Iterable[ExactScalar]) -> ExactPolynomial:
    coeffs = tuple(_fraction(value) for value in values)
    if not coeffs:
        raise ValueError("polynomial coefficients must be non-empty")
    last = len(coeffs) - 1
    while last > 0 and coeffs[last] == 0:
        last -= 1
    return coeffs[: last + 1]


def exact_coefficients(values: Iterable[ExactScalar]) -> ExactPolynomial:
    coeffs = _coerce_polynomial(values)
    if len(coeffs) < 2:
        raise ValueError("polynomial degree must be at least one")
    return coeffs


def _trim(values: Sequence[Fraction]) -> ExactPolynomial:
    coeffs = tuple(values)
    if not coeffs:
        return (Fraction(0),)
    last = len(coeffs) - 1
    while last > 0 and coeffs[last] == 0:
        last -= 1
    return coeffs[: last + 1]


def exact_derivative(coefficients: Iterable[ExactScalar]) -> ExactPolynomial:
    coeffs = exact_coefficients(coefficients)
    return tuple(Fraction(index) * coeffs[index] for index in range(1, len(coeffs)))


def exact_polydivmod(
    dividend: Sequence[Fraction],
    divisor: Sequence[Fraction],
) -> tuple[ExactPolynomial, ExactPolynomial]:
    """Exact polynomial long division in ascending coefficient convention."""
    numerator = list(_trim(dividend))
    denominator = _trim(divisor)
    if len(denominator) == 1 and denominator[0] == 0:
        raise ZeroDivisionError("polynomial division by zero")
    if len(numerator) < len(denominator):
        return (Fraction(0),), tuple(numerator)

    quotient = [Fraction(0)] * (len(numerator) - len(denominator) + 1)
    denominator_degree = len(denominator) - 1
    while len(numerator) >= len(denominator) and not (
        len(numerator) == 1 and numerator[0] == 0
    ):
        degree_gap = len(numerator) - len(denominator)
        factor = numerator[-1] / denominator[-1]
        quotient[degree_gap] += factor
        for index in range(denominator_degree + 1):
            numerator[degree_gap + index] -= factor * denominator[index]
        numerator = list(_trim(numerator))
        if len(numerator) == 1 and numerator[0] == 0:
            break
    return _trim(quotient), _trim(numerator)


def exact_monic_gcd(
    first: Sequence[Fraction],
    second: Sequence[Fraction],
) -> ExactPolynomial:
    """Euclidean gcd normalized to monic form."""
    a = _trim(first)
    b = _trim(second)
    if len(a) == 1 and a[0] == 0:
        if len(b) == 1 and b[0] == 0:
            return (Fraction(0),)
        return tuple(value / b[-1] for value in b)
    while not (len(b) == 1 and b[0] == 0):
        _, remainder = exact_polydivmod(a, b)
        a, b = b, remainder
    leading = a[-1]
    return tuple(value / leading for value in a)


def _sylvester_matrix(
    first: Sequence[Fraction],
    second: Sequence[Fraction],
) -> list[list[Fraction]]:
    first = _trim(first)
    second = _trim(second)
    degree_first = len(first) - 1
    degree_second = len(second) - 1
    size = degree_first + degree_second
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    first_descending = tuple(reversed(first))
    second_descending = tuple(reversed(second))
    for row in range(degree_second):
        for offset, value in enumerate(first_descending):
            matrix[row][row + offset] = value
    for block_row in range(degree_first):
        row = degree_second + block_row
        for offset, value in enumerate(second_descending):
            matrix[row][block_row + offset] = value
    return matrix


def exact_determinant(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    """Fraction-preserving Gaussian determinant with row pivoting."""
    size = len(matrix)
    if size == 0:
        return Fraction(1)
    if any(len(row) != size for row in matrix):
        raise ValueError("matrix must be square")
    work = [list(row) for row in matrix]
    determinant = Fraction(1)
    sign = 1
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign *= -1
        pivot_value = work[column][column]
        determinant *= pivot_value
        for row in range(column + 1, size):
            if work[row][column] == 0:
                continue
            factor = work[row][column] / pivot_value
            for index in range(column + 1, size):
                work[row][index] -= factor * work[column][index]
            work[row][column] = Fraction(0)
    return determinant if sign > 0 else -determinant


def exact_resultant(
    first_coefficients: Iterable[ExactScalar],
    second_coefficients: Iterable[ExactScalar],
) -> Fraction:
    """Exact resultant; either operand may be a non-zero constant polynomial."""
    first = _coerce_polynomial(first_coefficients)
    second = _coerce_polynomial(second_coefficients)
    if len(first) == 1 and first[0] == 0:
        raise ValueError("resultant with the zero polynomial is undefined here")
    if len(second) == 1 and second[0] == 0:
        raise ValueError("resultant with the zero polynomial is undefined here")
    degree_first = len(first) - 1
    degree_second = len(second) - 1
    if degree_first == 0:
        return first[0] ** degree_second
    if degree_second == 0:
        return second[0] ** degree_first
    return exact_determinant(_sylvester_matrix(first, second))


def exact_discriminant(coefficients: Iterable[ExactScalar]) -> Fraction:
    coeffs = exact_coefficients(coefficients)
    degree = len(coeffs) - 1
    if degree == 1:
        return Fraction(1)
    derivative = exact_derivative(coeffs)
    sign = -1 if (degree * (degree - 1) // 2) % 2 else 1
    return Fraction(sign) * exact_resultant(coeffs, derivative) / coeffs[-1]


def exact_newton_power_sums(
    coefficients: Iterable[ExactScalar],
    max_order: int,
) -> tuple[Fraction, ...]:
    """Exact Newton sums ``[p0,...,pM]`` with ``p0=degree``."""
    coeffs = exact_coefficients(coefficients)
    if max_order < 0:
        raise ValueError("max_order must be non-negative")
    degree = len(coeffs) - 1
    normalized_descending = tuple(value / coeffs[-1] for value in reversed(coeffs))
    sums = [Fraction(0)] * (max_order + 1)
    sums[0] = Fraction(degree)
    for order in range(1, max_order + 1):
        if order <= degree:
            total = sum(
                normalized_descending[index] * sums[order - index]
                for index in range(1, order)
            )
            total += Fraction(order) * normalized_descending[order]
        else:
            total = sum(
                normalized_descending[index] * sums[order - index]
                for index in range(1, degree + 1)
            )
        sums[order] = -total
    return tuple(sums)


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class ExactAlgebraAudit:
    degree: int
    discriminant: Fraction
    derivative_gcd: ExactPolynomial
    repeated_factor_degree: int
    square_free: bool
    power_sums: tuple[Fraction, ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "degree": self.degree,
            "discriminant": _fraction_text(self.discriminant),
            "derivative_gcd": [_fraction_text(value) for value in self.derivative_gcd],
            "repeated_factor_degree": self.repeated_factor_degree,
            "square_free": self.square_free,
            "power_sums": [_fraction_text(value) for value in self.power_sums],
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_exact_algebra(
    coefficients: Iterable[ExactScalar],
    *,
    power_sum_order: int | None = None,
) -> ExactAlgebraAudit:
    coeffs = exact_coefficients(coefficients)
    degree = len(coeffs) - 1
    derivative = exact_derivative(coeffs)
    gcd = exact_monic_gcd(coeffs, derivative)
    repeated_degree = max(len(gcd) - 1, 0)
    discriminant = exact_discriminant(coeffs)
    square_free = repeated_degree == 0
    order = 2 * degree if power_sum_order is None else int(power_sum_order)
    if order < 0:
        raise ValueError("power_sum_order must be non-negative")
    sums = exact_newton_power_sums(coeffs, order)
    if square_free != (discriminant != 0):
        status = "OAK_FAIL_EXACT_GCD_DISCRIMINANT_CONSISTENCY"
    elif square_free:
        status = "OAK_PASS_EXACT_SQUARE_FREE"
    else:
        status = "OAK_PASS_EXACT_REPEATED_FACTOR"
    return ExactAlgebraAudit(
        degree=degree,
        discriminant=discriminant,
        derivative_gcd=gcd,
        repeated_factor_degree=repeated_degree,
        square_free=square_free,
        power_sums=sums,
        status=status,
    )
