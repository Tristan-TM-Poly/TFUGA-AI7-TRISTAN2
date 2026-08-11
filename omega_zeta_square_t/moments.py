"""Finite moment/Hankel diagnostics for Ω-ZETA-SQUARE-T∞.

These routines deliberately report only finite numerical evidence. They never
promote finite positivity checks to a proof of the Riemann Hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class FiniteStieltjesReport:
    gammas_checked: int
    max_moment_order: int
    hankel_size: int
    moments: tuple[float, ...]
    hankel0_minors: tuple[float, ...]
    hankel1_minors: tuple[float, ...]
    hankel0_psd: bool
    hankel1_psd: bool
    finite_positive: bool
    epistemic_status: str = "NUMERICALLY_VERIFIED_FINITE_ONLY"
    proves_rh: bool = False


def _validated_gammas(gammas: Iterable[float]) -> List[float]:
    out = []
    for gamma in gammas:
        g = float(gamma)
        if not isfinite(g) or g <= 0.0:
            raise ValueError("all gamma values must be finite and strictly positive")
        out.append(g)
    if not out:
        raise ValueError("at least one gamma value is required")
    return out


def inverse_even_moments(gammas: Iterable[float], max_k: int) -> List[float]:
    """Return p_k=sum gamma^(-2k), k=1..max_k, for a finite sample."""

    if not isinstance(max_k, int) or max_k < 1:
        raise ValueError("max_k must be a positive integer")
    values = _validated_gammas(gammas)
    return [sum(g ** (-2 * k) for g in values) for k in range(1, max_k + 1)]


def hankel_matrix(moments: Sequence[float], size: int, shift: int = 0) -> List[List[float]]:
    """Build H[i,j]=m_{i+j+shift} from a zero-based moment sequence."""

    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    if not isinstance(shift, int) or shift < 0:
        raise ValueError("shift must be a non-negative integer")
    needed = 2 * size - 1 + shift
    if len(moments) < needed:
        raise ValueError(f"need at least {needed} moments for size={size}, shift={shift}")
    return [[float(moments[i + j + shift]) for j in range(size)] for i in range(size)]


def determinant(matrix: Sequence[Sequence[float]]) -> float:
    """Small dense determinant with partial pivoting, dependency-free."""

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    a = [[float(x) for x in row] for row in matrix]
    sign = 1.0
    det = 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if a[pivot][col] == 0.0:
            return 0.0
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            sign *= -1.0
        pivot_value = a[col][col]
        det *= pivot_value
        for row in range(col + 1, n):
            factor = a[row][col] / pivot_value
            for j in range(col + 1, n):
                a[row][j] -= factor * a[col][j]
    return sign * det


def leading_principal_minors(matrix: Sequence[Sequence[float]]) -> List[float]:
    """Return determinants of the 1x1 ... nxn leading principal blocks.

    These are retained as diagnostics only. Nonnegative leading principal
    minors alone do *not* certify positive semidefiniteness.
    """

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    return [determinant([row[:k] for row in matrix[:k]]) for k in range(1, n + 1)]


def ldlt_psd(matrix: Sequence[Sequence[float]], rel_tol: float = 1e-12) -> bool:
    """Numerically test symmetric PSD structure with an LDL^T recursion.

    A zero pivot is admissible only when the corresponding residual column is
    also zero within tolerance. This catches false positives that a
    leading-principal-minor-only check can miss. It remains a finite numerical
    diagnostic, not a proof certificate.
    """

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    a = [[float(x) for x in row] for row in matrix]
    scale = max(1.0, max(abs(x) for row in a for x in row))
    tol = rel_tol * scale
    for i in range(n):
        for j in range(i + 1, n):
            if abs(a[i][j] - a[j][i]) > tol:
                return False

    l = [[0.0] * n for _ in range(n)]
    d = [0.0] * n
    for i in range(n):
        l[i][i] = 1.0

    for k in range(n):
        pivot = a[k][k] - sum(l[k][s] * l[k][s] * d[s] for s in range(k))
        if pivot < -tol:
            return False
        residuals = [
            a[i][k] - sum(l[i][s] * l[k][s] * d[s] for s in range(k))
            for i in range(k + 1, n)
        ]
        if abs(pivot) <= tol:
            d[k] = 0.0
            if any(abs(r) > tol for r in residuals):
                return False
            continue
        d[k] = pivot
        for offset, i in enumerate(range(k + 1, n)):
            l[i][k] = residuals[offset] / pivot
    return True


def finite_stieltjes_report(gammas: Iterable[float], hankel_size: int = 3) -> FiniteStieltjesReport:
    """Run finite Stieltjes/Hankel checks on supplied positive ordinates.

    We use m_k = sum gamma^(-2(k+1)). The two standard finite Hankel families
    H^(0)=[m_{i+j}] and H^(1)=[m_{i+j+1}] are tested by a PSD-aware LDL^T
    recursion. Leading principal minors are still reported for observability,
    but are not used as the sole PSD criterion.
    """

    values = _validated_gammas(gammas)
    if not isinstance(hankel_size, int) or hankel_size < 1:
        raise ValueError("hankel_size must be a positive integer")
    needed = 2 * hankel_size
    moments = inverse_even_moments(values, needed)
    h0 = hankel_matrix(moments, hankel_size, shift=0)
    h1 = hankel_matrix(moments, hankel_size, shift=1)
    minors0 = leading_principal_minors(h0)
    minors1 = leading_principal_minors(h1)
    h0_psd = ldlt_psd(h0)
    h1_psd = ldlt_psd(h1)
    return FiniteStieltjesReport(
        gammas_checked=len(values),
        max_moment_order=needed,
        hankel_size=hankel_size,
        moments=tuple(moments),
        hankel0_minors=tuple(minors0),
        hankel1_minors=tuple(minors1),
        hankel0_psd=h0_psd,
        hankel1_psd=h1_psd,
        finite_positive=h0_psd and h1_psd,
    )
