"""Convert R11 normalized-Theta polynomial constraints to xi-derivative form.

If
    a_j = d_(2j) / ((2j)! d_0),   d_(2j)=xi^(2j)(1/2),
then any polynomial P(a) can be written
    P(a) = Q(d_0,d_2,...)/(L d_0^D)
with L>0 integer and Q an integer polynomial. Since d_0=xi(1/2)>0,
P and Q have the same sign.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import factorial, gcd
from typing import Mapping

from .symbolic_hankel import Exponent, Polynomial, hankel_determinant_polynomial

DerivativeExponent = tuple[int, ...]  # d0,d2,d4,...


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b) if a and b else 0


@dataclass(frozen=True)
class XiDerivativeTerm:
    coefficient: int
    exponents: DerivativeExponent

    @property
    def monomial(self) -> str:
        names = ["d0"] + [f"d{2*j}" for j in range(1, len(self.exponents))]
        factors: list[str] = []
        for name, power in zip(names, self.exponents):
            if power == 1:
                factors.append(name)
            elif power > 1:
                factors.append(f"{name}^{power}")
        return "*".join(factors) if factors else "1"


@dataclass(frozen=True)
class XiDerivativeConstraint:
    size: int
    shift: int
    common_integer_scale: int
    d0_power_denominator: int
    terms: tuple[XiDerivativeTerm, ...]
    relation: str = ">= 0"
    assumes_d0_positive: bool = True
    epistemic_status: str = "EXACT_FINITE_XI_DERIVATIVE_OBLIGATION_ONLY"
    proves_rh: bool = False


def theta_polynomial_to_xi_integer_polynomial(
    poly: Mapping[Exponent, Fraction],
) -> tuple[int, int, dict[DerivativeExponent, int]]:
    """Return (L,D,Q) with P(a)=Q(d)/(L*d0^D)."""

    if not poly:
        return 1, 0, {}
    nvars = len(next(iter(poly)))
    if any(len(exp) != nvars for exp in poly):
        raise ValueError("inconsistent exponent dimensions")
    max_degree = max(sum(exp) for exp in poly)
    rational_terms: dict[DerivativeExponent, Fraction] = {}
    for exp, coefficient in poly.items():
        degree = sum(exp)
        derivative_exp = (max_degree - degree,) + tuple(exp)
        factorial_den = 1
        for j, power in enumerate(exp, start=1):
            factorial_den *= factorial(2 * j) ** power
        coeff = coefficient / factorial_den
        rational_terms[derivative_exp] = rational_terms.get(derivative_exp, Fraction(0)) + coeff

    scale = 1
    for coefficient in rational_terms.values():
        scale = _lcm(scale, coefficient.denominator)
    integer_terms = {
        exp: int(coefficient * scale)
        for exp, coefficient in rational_terms.items()
        if coefficient
    }
    return scale, max_degree, integer_terms


def xi_derivative_constraint(size: int, shift: int = 0) -> XiDerivativeConstraint:
    poly = hankel_determinant_polynomial(size, shift)
    scale, degree, integer_terms = theta_polynomial_to_xi_integer_polynomial(poly)
    terms = tuple(
        XiDerivativeTerm(coefficient, exp)
        for exp, coefficient in sorted(integer_terms.items(), key=lambda item: (sum(item[0]), item[0]))
    )
    return XiDerivativeConstraint(
        size=size,
        shift=shift,
        common_integer_scale=scale,
        d0_power_denominator=degree,
        terms=terms,
    )
