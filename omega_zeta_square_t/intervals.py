"""Rigorous rational interval propagation for Ω-ZETA-SQUARE-T∞.

This layer propagates *supplied* rational enclosures. It does not itself create
certified analytic enclosures for xi derivatives. That source-certification step
remains an explicit research obligation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, permutations
from math import factorial
from typing import Sequence

Rational = int | Fraction


def _q(value: Rational) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not a rational endpoint")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    raise TypeError("rigorous interval endpoints must be int or Fraction")


@dataclass(frozen=True)
class RationalInterval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self):
        lo = _q(self.lower)
        hi = _q(self.upper)
        if lo > hi:
            raise ValueError("interval lower bound exceeds upper bound")
        object.__setattr__(self, "lower", lo)
        object.__setattr__(self, "upper", hi)

    @classmethod
    def point(cls, value: Rational) -> "RationalInterval":
        q = _q(value)
        return cls(q, q)

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    def contains_zero(self) -> bool:
        return self.lower <= 0 <= self.upper

    def __neg__(self) -> "RationalInterval":
        return RationalInterval(-self.upper, -self.lower)

    def __add__(self, other) -> "RationalInterval":
        other = as_interval(other)
        return RationalInterval(self.lower + other.lower, self.upper + other.upper)

    __radd__ = __add__

    def __sub__(self, other) -> "RationalInterval":
        return self + (-as_interval(other))

    def __rsub__(self, other) -> "RationalInterval":
        return as_interval(other) - self

    def __mul__(self, other) -> "RationalInterval":
        other = as_interval(other)
        products = (
            self.lower * other.lower,
            self.lower * other.upper,
            self.upper * other.lower,
            self.upper * other.upper,
        )
        return RationalInterval(min(products), max(products))

    __rmul__ = __mul__

    def reciprocal(self) -> "RationalInterval":
        if self.contains_zero():
            raise ZeroDivisionError("cannot invert an interval containing zero")
        values = (Fraction(1, 1) / self.lower, Fraction(1, 1) / self.upper)
        return RationalInterval(min(values), max(values))

    def __truediv__(self, other) -> "RationalInterval":
        return self * as_interval(other).reciprocal()

    def __rtruediv__(self, other) -> "RationalInterval":
        return as_interval(other) / self


def as_interval(value: Rational | RationalInterval) -> RationalInterval:
    if isinstance(value, RationalInterval):
        return value
    return RationalInterval.point(value)


@dataclass(frozen=True)
class IntervalMinor:
    indices: tuple[int, ...]
    determinant: RationalInterval
    sign: str


@dataclass(frozen=True)
class IntervalPSDReport:
    size: int
    certified_psd: bool
    certified_not_psd: bool
    unresolved: bool
    minors: tuple[IntervalMinor, ...]
    epistemic_status: str = "RIGOROUS_FOR_SUPPLIED_INTERVAL_ENCLOSURES_ONLY"
    proves_rh: bool = False


@dataclass(frozen=True)
class IntervalStieltjesCertificate:
    hankel_size: int
    h0: IntervalPSDReport
    h1: IntervalPSDReport
    certified_finite_positive: bool
    certified_finite_violation: bool
    unresolved: bool
    source_obligation: str = "certified analytic enclosures for the supplied moment/xi inputs"
    proves_rh: bool = False


def normalized_theta_intervals_from_xi_even_derivatives(
    derivative_intervals: Sequence[RationalInterval],
) -> list[RationalInterval]:
    """Propagate xi^(2m)(1/2) intervals to Theta(u)/Theta(0) coefficients."""

    if not derivative_intervals:
        raise ValueError("at least xi(1/2) interval is required")
    d0 = as_interval(derivative_intervals[0])
    if d0.contains_zero():
        raise ValueError("xi(1/2) enclosure must exclude zero")
    out = [RationalInterval.point(1)]
    for m in range(1, len(derivative_intervals)):
        dm = as_interval(derivative_intervals[m])
        out.append(dm / RationalInterval.point(factorial(2 * m)) / d0)
    return out


def log_derivative_interval_coefficients(
    normalized_coeffs: Sequence[RationalInterval],
) -> list[RationalInterval]:
    if not normalized_coeffs:
        raise ValueError("normalized coefficients are required")
    a = [as_interval(x) for x in normalized_coeffs]
    if a[0] != RationalInterval.point(1):
        raise ValueError("normalized coefficient a0 must be the exact point interval 1")
    q: list[RationalInterval] = []
    for n in range(len(a) - 1):
        value = RationalInterval.point(n + 1) * a[n + 1]
        for j in range(1, n + 1):
            value = value - a[j] * q[n - j]
        q.append(value)
    return q


def inverse_moment_intervals_from_theta_coeffs(
    normalized_coeffs: Sequence[RationalInterval],
) -> list[RationalInterval]:
    q = log_derivative_interval_coefficients(normalized_coeffs)
    return [value if n % 2 == 0 else -value for n, value in enumerate(q)]


def inverse_moment_intervals_from_xi_even_derivatives(
    derivative_intervals: Sequence[RationalInterval],
) -> list[RationalInterval]:
    return inverse_moment_intervals_from_theta_coeffs(
        normalized_theta_intervals_from_xi_even_derivatives(derivative_intervals)
    )


def interval_hankel_matrix(
    moments: Sequence[RationalInterval], size: int, shift: int = 0
) -> list[list[RationalInterval]]:
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    needed = 2 * size - 1 + shift
    if len(moments) < needed:
        raise ValueError(f"need at least {needed} moments")
    values = [as_interval(x) for x in moments]
    return [[values[i + j + shift] for j in range(size)] for i in range(size)]


def _permutation_sign(p: tuple[int, ...]) -> int:
    inversions = sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
    return -1 if inversions % 2 else 1


def interval_determinant(
    matrix: Sequence[Sequence[RationalInterval]], max_size: int = 6
) -> RationalInterval:
    """Rigorous determinant enclosure by Leibniz expansion.

    This is factorial-time but correlation-safe and dependency-free. The cap is
    intentional; larger certificates should use a dedicated verified interval
    linear-algebra backend.
    """

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if n > max_size:
        raise ValueError(f"interval determinant mode is capped at size {max_size}")
    a = [[as_interval(x) for x in row] for row in matrix]
    total = RationalInterval.point(0)
    for p in permutations(range(n)):
        term = RationalInterval.point(1)
        for i, j in enumerate(p):
            term = term * a[i][j]
        total = total + term if _permutation_sign(p) > 0 else total - term
    return total


def interval_psd_report(
    matrix: Sequence[Sequence[RationalInterval]], max_size: int = 6
) -> IntervalPSDReport:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if n > max_size:
        raise ValueError(f"interval all-principal-minor mode is capped at size {max_size}")
    minors: list[IntervalMinor] = []
    for k in range(1, n + 1):
        for idx in combinations(range(n), k):
            sub = [[matrix[i][j] for j in idx] for i in idx]
            det = interval_determinant(sub, max_size=max_size)
            if det.lower >= 0:
                sign = "CERTIFIED_NONNEGATIVE"
            elif det.upper < 0:
                sign = "CERTIFIED_NEGATIVE"
            else:
                sign = "UNRESOLVED"
            minors.append(IntervalMinor(tuple(idx), det, sign))
    certified_psd = all(m.sign == "CERTIFIED_NONNEGATIVE" for m in minors)
    certified_not_psd = any(m.sign == "CERTIFIED_NEGATIVE" for m in minors)
    return IntervalPSDReport(
        size=n,
        certified_psd=certified_psd,
        certified_not_psd=certified_not_psd,
        unresolved=not certified_psd and not certified_not_psd,
        minors=tuple(minors),
    )


def interval_stieltjes_certificate(
    inverse_moment_intervals: Sequence[RationalInterval], hankel_size: int = 2
) -> IntervalStieltjesCertificate:
    h0 = interval_psd_report(
        interval_hankel_matrix(inverse_moment_intervals, hankel_size, shift=0)
    )
    h1 = interval_psd_report(
        interval_hankel_matrix(inverse_moment_intervals, hankel_size, shift=1)
    )
    positive = h0.certified_psd and h1.certified_psd
    violation = h0.certified_not_psd or h1.certified_not_psd
    return IntervalStieltjesCertificate(
        hankel_size=hankel_size,
        h0=h0,
        h1=h1,
        certified_finite_positive=positive,
        certified_finite_violation=violation,
        unresolved=not positive and not violation,
    )
