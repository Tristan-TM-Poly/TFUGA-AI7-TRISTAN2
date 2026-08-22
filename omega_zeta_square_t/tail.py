"""Rigorous finite-to-infinite Hankel witness stability bounds.

For a finite real Hankel contribution A and real polynomial coefficient vector
v, the quadratic value q=v^T A v can be certified negative exactly.  A remaining
conjugation-symmetric spectral tail contributes

    sum_j lambda_j P_v(lambda_j)^2.

If |lambda_j|<=R and sum_j |lambda_j|<=M, then its absolute contribution is at
most M (sum_i |v_i| R^i)^2.  A strict negative margin larger than this bound
survives addition of the full tail.

The theorem is rigorous conditional on certified R and M bounds.  It does not
produce those analytic Riemann-tail bounds itself and never claims RH.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

Rational = int | Fraction


def _q(value: Rational) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not a rational value")
    return value if isinstance(value, Fraction) else Fraction(value, 1)


def exact_quadratic_form(
    matrix: Sequence[Sequence[Rational]], vector: Sequence[Rational]
) -> Fraction:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if len(vector) != n:
        raise ValueError("vector length must match matrix size")
    v = tuple(_q(x) for x in vector)
    return sum(
        v[i] * _q(matrix[i][j]) * v[j]
        for i in range(n)
        for j in range(n)
    )


def polynomial_abs_bound(vector: Sequence[Rational], radius_upper: Rational) -> Fraction:
    """Return sum |v_i| R^i, an upper bound for |P_v(z)| on |z|<=R."""

    radius = _q(radius_upper)
    if radius < 0:
        raise ValueError("radius_upper must be non-negative")
    return sum(abs(_q(value)) * radius**i for i, value in enumerate(vector))


@dataclass(frozen=True)
class TailStabilityCertificate:
    finite_quadratic_value: Fraction
    negative_margin: Fraction
    tail_radius_upper: Fraction
    tail_abs_mass_upper: Fraction
    polynomial_abs_upper: Fraction
    tail_quadratic_abs_upper: Fraction
    residual_negative_margin: Fraction
    certified_indefinite_after_tail: bool
    input_tail_bounds_must_be_certified: bool = True
    epistemic_status: str = "RIGOROUS_CONDITIONAL_FINITE_TO_INFINITE_WITNESS"
    proves_rh: bool = False


def tail_stability_certificate(
    finite_matrix: Sequence[Sequence[Rational]],
    witness_vector: Sequence[Rational],
    *,
    tail_radius_upper: Rational,
    tail_abs_mass_upper: Rational,
) -> TailStabilityCertificate:
    """Certify survival of a negative quadratic witness under a bounded tail."""

    radius = _q(tail_radius_upper)
    mass = _q(tail_abs_mass_upper)
    if radius < 0 or mass < 0:
        raise ValueError("tail bounds must be non-negative")
    finite_q = exact_quadratic_form(finite_matrix, witness_vector)
    margin = -finite_q if finite_q < 0 else Fraction(0)
    poly = polynomial_abs_bound(witness_vector, radius)
    tail_bound = mass * poly * poly
    residual = margin - tail_bound
    certified = finite_q < 0 and residual > 0
    return TailStabilityCertificate(
        finite_quadratic_value=finite_q,
        negative_margin=margin,
        tail_radius_upper=radius,
        tail_abs_mass_upper=mass,
        polynomial_abs_upper=poly,
        tail_quadratic_abs_upper=tail_bound,
        residual_negative_margin=residual,
        certified_indefinite_after_tail=certified,
    )


def negative_witness_from_indefinite_2x2(
    matrix: Sequence[Sequence[Rational]],
) -> tuple[Fraction, Fraction]:
    """Construct an exact witness for [[a,b],[b,c]] when a>0 and det<0.

    The vector (-b,a) has quadratic value a*(a*c-b^2), hence is strictly
    negative under those hypotheses.
    """

    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise ValueError("matrix must be 2x2")
    a = _q(matrix[0][0])
    b = _q(matrix[0][1])
    c = _q(matrix[1][1])
    if _q(matrix[1][0]) != b:
        raise ValueError("matrix must be symmetric")
    det = a * c - b * b
    if a <= 0 or det >= 0:
        raise ValueError("requires a>0 and negative determinant")
    return -b, a
