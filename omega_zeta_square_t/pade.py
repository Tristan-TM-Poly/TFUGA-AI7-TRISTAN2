"""Padé/Stieltjes reconstruction from inverse-moment series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PadeApproximant(Generic[T]):
    numerator: tuple[T, ...]
    denominator: tuple[T, ...]
    m: int
    n: int
    epistemic_status: str = "FORMAL_SERIES_RECONSTRUCTION"
    proves_rh: bool = False

    def evaluate(self, u: T) -> T:
        def horner(coeffs: tuple[T, ...]) -> T:
            value = coeffs[-1]
            for c in reversed(coeffs[:-1]):
                value = value * u + c
            return value

        return horner(self.numerator) / horner(self.denominator)


def _solve_linear(a: Sequence[Sequence[T]], b: Sequence[T]) -> list[T]:
    n = len(a)
    if n == 0 or len(b) != n or any(len(row) != n for row in a):
        raise ValueError("linear system must be non-empty and square")
    aug = [list(row) + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if aug[r][col] != 0), None)
        if pivot is None:
            raise ValueError("singular Padé reconstruction system")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        p = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= p
        for r in range(n):
            if r == col or aug[r][col] == 0:
                continue
            factor = aug[r][col]
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def pade_from_series(coeffs: Sequence[T], m: int, n: int) -> PadeApproximant[T]:
    """Construct [m/n] Padé approximant for F(u)=sum c_k u^k.

    Q(0)=1. At least m+n+1 series coefficients are required.
    """

    if m < 0 or n < 1:
        raise ValueError("require m >= 0 and n >= 1")
    if len(coeffs) < m + n + 1:
        raise ValueError("insufficient series coefficients for requested Padé order")

    a: list[list[T]] = []
    b: list[T] = []
    for k in range(m + 1, m + n + 1):
        a.append([coeffs[k - j] for j in range(1, n + 1)])
        b.append(-coeffs[k])
    q_tail = _solve_linear(a, b)
    q = [1] + q_tail

    p: list[T] = []
    for k in range(m + 1):
        value = 0
        for j in range(min(k, n) + 1):
            value += q[j] * coeffs[k - j]
        p.append(value)
    return PadeApproximant(tuple(p), tuple(q), m=m, n=n)


def stieltjes_series_from_inverse_moments(inverse_moments: Sequence[T]) -> list[T]:
    """Convert p_1,p_2,... to L(u)=p_1-p_2 u+p_3 u^2-... coefficients."""

    if not inverse_moments:
        raise ValueError("at least one inverse moment is required")
    return [value if k % 2 == 0 else -value for k, value in enumerate(inverse_moments)]


def stieltjes_pade_from_inverse_moments(
    inverse_moments: Sequence[T], order: int
) -> PadeApproximant[T]:
    """Construct the canonical [order-1/order] Padé approximant to L(u)."""

    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")
    if len(inverse_moments) < 2 * order:
        raise ValueError(f"need at least {2 * order} inverse moments")
    series = stieltjes_series_from_inverse_moments(inverse_moments)
    return pade_from_series(series, m=order - 1, n=order)
