"""Compile all finite R10 Hankel principal-minor constraints exactly."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .symbolic_hankel import (
    HankelPolynomialConstraint,
    Polynomial,
    TensorLiftTerm,
    determinant_polynomial,
    newton_power_sum_polynomials,
)


@dataclass(frozen=True)
class PrincipalMinorConstraint:
    full_size: int
    shift: int
    indices: tuple[int, ...]
    terms: tuple[TensorLiftTerm, ...]
    relation: str = ">= 0"
    epistemic_status: str = "EXACT_FINITE_PSD_OBLIGATION_ONLY"
    proves_rh: bool = False

    @property
    def order(self) -> int:
        return len(self.indices)

    @property
    def term_count(self) -> int:
        return len(self.terms)


def hankel_principal_minor_polynomial(
    full_size: int,
    indices: tuple[int, ...],
    shift: int = 0,
) -> Polynomial:
    if not isinstance(full_size, int) or full_size < 1:
        raise ValueError("full_size must be positive")
    if full_size > 5:
        raise ValueError("principal-minor compiler capped at full_size 5")
    if not indices:
        raise ValueError("indices must be non-empty")
    if tuple(sorted(set(indices))) != indices:
        raise ValueError("indices must be unique and strictly increasing")
    if indices[0] < 0 or indices[-1] >= full_size:
        raise ValueError("principal index out of range")
    if not isinstance(shift, int) or shift < 0:
        raise ValueError("shift must be a non-negative integer")

    max_p = 2 * (full_size - 1) + shift + 1
    p = newton_power_sum_polynomials(max_p)
    matrix = [
        [p[i + j + shift] for j in indices]
        for i in indices
    ]
    return determinant_polynomial(matrix)


def all_principal_minor_constraints(
    full_size: int,
    shift: int = 0,
) -> tuple[PrincipalMinorConstraint, ...]:
    """Return all 2^N-1 principal-minor inequalities for H_N^(shift)."""

    if not isinstance(full_size, int) or not 1 <= full_size <= 5:
        raise ValueError("full_size must be an integer in 1..5")
    constraints: list[PrincipalMinorConstraint] = []
    for order in range(1, full_size + 1):
        for indices in combinations(range(full_size), order):
            poly = hankel_principal_minor_polynomial(full_size, indices, shift)
            terms = tuple(
                TensorLiftTerm(coeff, exp)
                for exp, coeff in sorted(
                    poly.items(), key=lambda item: (sum(item[0]), item[0])
                )
            )
            constraints.append(
                PrincipalMinorConstraint(
                    full_size=full_size,
                    shift=shift,
                    indices=indices,
                    terms=terms,
                )
            )
    return tuple(constraints)
