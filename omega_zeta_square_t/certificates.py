"""Exact finite certificates for Stieltjes/Hankel constraints.

Exact here means exact for the supplied rational moment data. It does not mean
that approximate moments have been certified as exact values of xi/zeta data.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Iterable, Sequence

RationalInput = int | Fraction


@dataclass(frozen=True)
class PrincipalMinor:
    indices: tuple[int, ...]
    determinant: Fraction


@dataclass(frozen=True)
class ExactPSDReport:
    size: int
    all_principal_minors_nonnegative: bool
    minors: tuple[PrincipalMinor, ...]
    epistemic_status: str = "EXACT_FOR_SUPPLIED_RATIONAL_DATA_ONLY"
    proves_rh: bool = False


@dataclass(frozen=True)
class ExactStieltjesCertificate:
    hankel_size: int
    h0: ExactPSDReport
    h1: ExactPSDReport
    finite_positive: bool
    epistemic_status: str = "EXACT_FINITE_MOMENT_CERTIFICATE_ONLY"
    proves_rh: bool = False


def _fraction(value: RationalInput) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean values are not accepted as rational moment data")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    raise TypeError("exact certification requires int or fractions.Fraction inputs")


def exact_hankel_matrix(
    moments: Sequence[RationalInput], size: int, shift: int = 0
) -> list[list[Fraction]]:
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    if not isinstance(shift, int) or shift < 0:
        raise ValueError("shift must be a non-negative integer")
    needed = 2 * size - 1 + shift
    if len(moments) < needed:
        raise ValueError(f"need at least {needed} moments for size={size}, shift={shift}")
    values = [_fraction(x) for x in moments]
    return [[values[i + j + shift] for j in range(size)] for i in range(size)]


def exact_determinant(matrix: Sequence[Sequence[RationalInput]]) -> Fraction:
    """Exact determinant by rational Gaussian elimination."""

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    a = [[_fraction(x) for x in row] for row in matrix]
    sign = 1
    det = Fraction(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if a[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            sign *= -1
        pivot_value = a[col][col]
        det *= pivot_value
        for row in range(col + 1, n):
            if a[row][col] == 0:
                continue
            factor = a[row][col] / pivot_value
            for j in range(col + 1, n):
                a[row][j] -= factor * a[col][j]
    return det if sign > 0 else -det


def exact_principal_minors(
    matrix: Sequence[Sequence[RationalInput]], max_size: int = 8
) -> tuple[PrincipalMinor, ...]:
    """Return every non-empty principal minor, exactly.

    The enumeration is exponential; max_size prevents accidental combinatorial
    blowups in CI/research automation.
    """

    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if n > max_size:
        raise ValueError(f"exact all-principal-minor mode is capped at size {max_size}")
    a = [[_fraction(x) for x in row] for row in matrix]
    out: list[PrincipalMinor] = []
    for k in range(1, n + 1):
        for idx in combinations(range(n), k):
            sub = [[a[i][j] for j in idx] for i in idx]
            out.append(PrincipalMinor(indices=tuple(idx), determinant=exact_determinant(sub)))
    return tuple(out)


def exact_psd_report(
    matrix: Sequence[Sequence[RationalInput]], max_size: int = 8
) -> ExactPSDReport:
    minors = exact_principal_minors(matrix, max_size=max_size)
    return ExactPSDReport(
        size=len(matrix),
        all_principal_minors_nonnegative=all(m.determinant >= 0 for m in minors),
        minors=minors,
    )


def exact_stieltjes_certificate(
    moments: Sequence[RationalInput], hankel_size: int = 3, max_size: int = 8
) -> ExactStieltjesCertificate:
    """Certify finite rational H^(0), H^(1) PSD constraints exactly."""

    h0 = exact_psd_report(
        exact_hankel_matrix(moments, hankel_size, shift=0), max_size=max_size
    )
    h1 = exact_psd_report(
        exact_hankel_matrix(moments, hankel_size, shift=1), max_size=max_size
    )
    return ExactStieltjesCertificate(
        hankel_size=hankel_size,
        h0=h0,
        h1=h1,
        finite_positive=h0.all_principal_minors_nonnegative
        and h1.all_principal_minors_nonnegative,
    )


def leading_only_false_positive_hankel() -> list[list[Fraction]]:
    """A concrete M- witness: leading minors >= 0 yet the matrix is not PSD.

    It is the 3x3 Hankel matrix generated by moments [0, 0, -3, -3, -3].
    Leading principal determinants are 0, 0, 27, but the principal minor on
    indices (0, 2) has determinant -9.
    """

    return exact_hankel_matrix([0, 0, -3, -3, -3], size=3)
