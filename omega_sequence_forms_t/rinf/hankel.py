"""Exact Hankel diagnostics, rank profiles and rational Prony reconstruction."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import gcd, isqrt
from typing import Iterable, Sequence

from ..exact import NumberLike, normalize_terms, solve_unique_linear_system, vector_complexity
from ..recurrence import detect_linear_recurrence


Matrix = tuple[tuple[Fraction, ...], ...]


@dataclass(frozen=True)
class HankelRankProfile:
    sizes: tuple[int, ...]
    ranks: tuple[int, ...]
    nullities: tuple[int, ...]
    stable_rank: int | None
    exact: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "sizes": list(self.sizes),
            "ranks": list(self.ranks),
            "nullities": list(self.nullities),
            "stable_rank": self.stable_rank,
            "exact": self.exact,
        }


@dataclass(frozen=True)
class RationalSpectralTerm:
    amplitude: Fraction
    root: Fraction

    def evaluate(self, n: int) -> Fraction:
        return self.amplitude * self.root**n

@dataclass(frozen=True)
class RationalPronyCandidate:
    terms: tuple[RationalSpectralTerm, ...]
    recurrence_coefficients: tuple[Fraction, ...]
    characteristic_coefficients: tuple[Fraction, ...]
    fitted_terms: int
    fitted_matches: int
    held_out_terms: int
    held_out_matches: int

    @property
    def rank(self) -> int:
        return len(self.terms)

    @property
    def predicts_holdout(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches

    @property
    def complexity(self) -> int:
        values = [term.amplitude for term in self.terms] + [term.root for term in self.terms]
        return self.rank + vector_complexity(values)

    def evaluate(self, n: int) -> Fraction:
        if n < 0:
            raise ValueError("n must be non-negative")
        return sum((term.evaluate(n) for term in self.terms), Fraction(0))

    def expression(self) -> str:
        return " + ".join(f"({term.amplitude})*({term.root})^n" for term in self.terms) or "0"

    def to_dict(self) -> dict[str, object]:
        return {
            "family": "rational_prony",
            "rank": self.rank,
            "terms": [
                {"amplitude": str(term.amplitude), "root": str(term.root)}
                for term in self.terms
            ],
            "recurrence_coefficients": [str(value) for value in self.recurrence_coefficients],
            "characteristic_coefficients": [str(value) for value in self.characteristic_coefficients],
            "expression": self.expression(),
            "complexity": self.complexity,
            "validation": {
                "fitted_terms": self.fitted_terms,
                "fitted_matches": self.fitted_matches,
                "held_out_terms": self.held_out_terms,
                "held_out_matches": self.held_out_matches,
            },
            "global_identity_proved": False,
        }


def hankel_matrix(
    terms: Iterable[NumberLike],
    rows: int,
    columns: int | None = None,
    *,
    offset: int = 0,
) -> Matrix:
    values = normalize_terms(terms)
    if rows <= 0:
        raise ValueError("rows must be positive")
    columns = rows if columns is None else columns
    if columns <= 0 or offset < 0:
        raise ValueError("invalid Hankel dimensions")
    required = offset + rows + columns - 1
    if required > len(values):
        raise ValueError(f"need {required} terms, received {len(values)}")
    return tuple(
        tuple(values[offset + row + column] for column in range(columns))
        for row in range(rows)
    )


def matrix_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    if not matrix:
        return 0
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("matrix must be rectangular")
    rows = [list(row) for row in matrix]
    rank = 0
    for column in range(width):
        pivot = next((index for index in range(rank, len(rows)) if rows[index][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        divisor = rows[rank][column]
        rows[rank] = [value / divisor for value in rows[rank]]
        for other in range(len(rows)):
            if other == rank:
                continue
            factor = rows[other][column]
            if factor:
                rows[other] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(rows[other], rows[rank])
                ]
        rank += 1
        if rank == len(rows):
            break
    return rank


def determinant(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    if not matrix:
        return Fraction(1)
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("determinant requires a square matrix")
    rows = [list(row) for row in matrix]
    result = Fraction(1)
    sign = 1
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            sign *= -1
        pivot_value = rows[column][column]
        result *= pivot_value
        for row in range(column + 1, size):
            factor = rows[row][column] / pivot_value
            for inner in range(column + 1, size):
                rows[row][inner] -= factor * rows[column][inner]
    return result * sign


def hankel_rank_profile(
    terms: Iterable[NumberLike],
    *,
    max_size: int | None = None,
    offset: int = 0,
) -> HankelRankProfile:
    values = normalize_terms(terms)
    available = len(values) - offset
    maximum = max(0, (available + 1) // 2)
    if max_size is not None:
        maximum = min(maximum, max_size)
    sizes = []
    ranks = []
    nullities = []
    for size in range(1, maximum + 1):
        matrix = hankel_matrix(values, size, offset=offset)
        rank = matrix_rank(matrix)
        sizes.append(size)
        ranks.append(rank)
        nullities.append(size - rank)
    stable_rank = None
    for index in range(len(ranks)):
        tail = ranks[index:]
        if len(tail) >= 2 and len(set(tail)) == 1:
            stable_rank = tail[0]
            break
    return HankelRankProfile(tuple(sizes), tuple(ranks), tuple(nullities), stable_rank)


def characteristic_from_recurrence(coefficients: Sequence[Fraction]) -> tuple[Fraction, ...]:
    """Return ascending coefficients of x^r-c1*x^(r-1)-...-cr."""

    order = len(coefficients)
    if order == 0:
        raise ValueError("recurrence must have positive order")
    ascending = [-coefficients[order - 1 - degree] for degree in range(order)]
    ascending.append(Fraction(1))
    return tuple(ascending)


def _divisors(value: int) -> tuple[int, ...]:
    value = abs(value)
    if value == 0:
        return (0,)
    result = set()
    for divisor in range(1, isqrt(value) + 1):
        if value % divisor == 0:
            result.add(divisor)
            result.add(value // divisor)
    return tuple(sorted(result))


def _integerize_polynomial(coefficients: Sequence[Fraction]) -> tuple[int, ...]:
    lcm = 1
    for value in coefficients:
        lcm = lcm * value.denominator // gcd(lcm, value.denominator)
    integers = [int(value * lcm) for value in coefficients]
    common = 0
    for value in integers:
        common = gcd(common, abs(value))
    if common:
        integers = [value // common for value in integers]
    if integers[-1] < 0:
        integers = [-value for value in integers]
    return tuple(integers)


def polynomial_value(coefficients: Sequence[Fraction], x: Fraction) -> Fraction:
    result = Fraction(0)
    for coefficient in reversed(coefficients):
        result = result * x + coefficient
    return result


def divide_by_linear(
    coefficients: Sequence[Fraction],
    root: Fraction,
) -> tuple[Fraction, ...]:
    """Divide ascending polynomial coefficients by (x-root)."""

    if len(coefficients) <= 1:
        raise ValueError("cannot divide a constant polynomial")
    descending = list(reversed(coefficients))
    quotient_desc = [descending[0]]
    for coefficient in descending[1:-1]:
        quotient_desc.append(coefficient + root * quotient_desc[-1])
    remainder = descending[-1] + root * quotient_desc[-1]
    if remainder != 0:
        raise ValueError("supplied value is not a root")
    return tuple(reversed(quotient_desc))


def rational_roots(coefficients: Sequence[Fraction]) -> tuple[Fraction, ...] | None:
    """Factor a polynomial completely into distinct rational roots.

    Returns ``None`` when the polynomial has a repeated root, an irrational or
    complex factor, or a zero leading coefficient.
    """

    polynomial = tuple(coefficients)
    if len(polynomial) <= 1 or polynomial[-1] == 0:
        return None
    roots: list[Fraction] = []
    while len(polynomial) > 1:
        integer = _integerize_polynomial(polynomial)
        constant = integer[0]
        leading = integer[-1]
        candidates = set()
        if constant == 0:
            candidates.add(Fraction(0))
        else:
            for numerator, denominator, sign in product(_divisors(constant), _divisors(leading), (-1, 1)):
                if denominator:
                    candidates.add(Fraction(sign * numerator, denominator))
        root = next((item for item in sorted(candidates) if polynomial_value(polynomial, item) == 0), None)
        if root is None or root in roots:
            return None
        roots.append(root)
        polynomial = divide_by_linear(polynomial, root)
    return tuple(roots)


def _fit_amplitudes(roots: Sequence[Fraction], terms: Sequence[Fraction], count: int) -> tuple[Fraction, ...] | None:
    if count < len(roots):
        return None
    matrix = [[root**n for root in roots] for n in range(count)]
    rhs = list(terms[:count])
    solution = solve_unique_linear_system(matrix, rhs)
    return None if solution is None else tuple(solution)


def discover_rational_prony(
    terms: Iterable[NumberLike],
    *,
    max_order: int = 12,
    holdout: int | None = None,
) -> tuple[RationalPronyCandidate, ...]:
    values = normalize_terms(terms)
    if holdout is None:
        holdout = 0 if len(values) < 10 else max(2, min(16, len(values) // 4))
    if not 0 <= holdout < len(values):
        raise ValueError("invalid holdout")
    training = values[: len(values) - holdout]
    recurrence = detect_linear_recurrence(training, max_order=max_order)
    if recurrence is None:
        return ()
    coefficients = tuple(recurrence)
    order = len(coefficients)
    characteristic = characteristic_from_recurrence(coefficients)
    roots = rational_roots(characteristic)
    if roots is None or len(roots) != order:
        return ()
    amplitudes = _fit_amplitudes(roots, training, len(training))
    if amplitudes is None:
        return ()
    spectral_terms = tuple(
        RationalSpectralTerm(amplitude=amplitude, root=root)
        for amplitude, root in zip(amplitudes, roots)
    )
    candidate = RationalPronyCandidate(
        terms=spectral_terms,
        recurrence_coefficients=coefficients,
        characteristic_coefficients=characteristic,
        fitted_terms=len(training),
        fitted_matches=sum(
            sum((term.evaluate(n) for term in spectral_terms), Fraction(0)) == training[n]
            for n in range(len(training))
        ),
        held_out_terms=holdout,
        held_out_matches=sum(
            sum((term.evaluate(n) for term in spectral_terms), Fraction(0)) == values[n]
            for n in range(len(training), len(values))
        ),
    )
    if candidate.fitted_matches != candidate.fitted_terms:
        return ()
    return (candidate,)
