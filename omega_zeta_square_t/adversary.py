"""Exact local adversary model for off-critical-line zero images.

For a centered-square zero image u=(delta+i gamma)^2 define lambda=-1/u.
Under RH delta=0 and lambda is positive real.  An off-line functional/conjugate
quartet becomes a non-real conjugate pair lambda, conjugate(lambda) in the
square quotient.

This module proves an exact *isolated-pair* Hankel identity. It is not a theorem
about the full Riemann zero set because all other zero contributions can change
finite Hankel determinants.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .certificates import exact_stieltjes_certificate

Rational = int | Fraction


def _q(value: Rational) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not a rational coordinate")
    return value if isinstance(value, Fraction) else Fraction(value, 1)


def lambda_pair_from_beta_gamma(
    beta: Rational, gamma: Rational
) -> tuple[Fraction, Fraction]:
    """Return exact (a,b) for lambda=-1/(rho-1/2)^2 = a+i b."""

    beta_q = _q(beta)
    gamma_q = _q(gamma)
    delta = beta_q - Fraction(1, 2)
    if delta == 0 and gamma_q == 0:
        raise ZeroDivisionError("centered zero image u=0 cannot be inverted")
    x = delta * delta - gamma_q * gamma_q
    y = 2 * delta * gamma_q
    denom = x * x + y * y
    return -x / denom, y / denom


def conjugate_pair_inverse_moments(
    a: Rational, b: Rational, max_k: int
) -> list[Fraction]:
    """Return p_k=(a+ib)^k+(a-ib)^k exactly, k=1..max_k."""

    if not isinstance(max_k, int) or max_k < 1:
        raise ValueError("max_k must be a positive integer")
    a_q, b_q = _q(a), _q(b)
    real, imag = Fraction(1), Fraction(0)
    out: list[Fraction] = []
    for _ in range(max_k):
        real, imag = real * a_q - imag * b_q, real * b_q + imag * a_q
        out.append(2 * real)
    return out


def conjugate_pair_hankel2_determinant(a: Rational, b: Rational) -> Fraction:
    """Exact det [[p1,p2],[p2,p3]] = -4 b^2(a^2+b^2)."""

    a_q, b_q = _q(a), _q(b)
    return -4 * b_q * b_q * (a_q * a_q + b_q * b_q)


def centered_pair_hankel2_determinant(
    beta: Rational, gamma: Rational
) -> Fraction:
    """Exact isolated-pair determinant in centered coordinates.

    If delta=beta-1/2, the result is
        -16 delta^2 gamma^2 / (delta^2+gamma^2)^6.
    It is strictly negative for delta != 0 and gamma != 0, and zero on the
    critical line.  This is a local pair identity, not a full-RH certificate.
    """

    beta_q, gamma_q = _q(beta), _q(gamma)
    delta = beta_q - Fraction(1, 2)
    radius2 = delta * delta + gamma_q * gamma_q
    if radius2 == 0:
        raise ZeroDivisionError("centered zero image u=0 cannot be inverted")
    return -16 * delta * delta * gamma_q * gamma_q / (radius2 ** 6)


def mixed_inverse_moments(
    positive_real_lambdas: Iterable[Rational],
    pair_a: Rational,
    pair_b: Rational,
    max_k: int,
) -> list[Fraction]:
    """Add positive-real background atoms to one conjugate-pair model."""

    pair = conjugate_pair_inverse_moments(pair_a, pair_b, max_k)
    reals = tuple(_q(value) for value in positive_real_lambdas)
    if any(value <= 0 for value in reals):
        raise ValueError("background lambda atoms must be positive")
    return [
        pair[k - 1] + sum(value**k for value in reals)
        for k in range(1, max_k + 1)
    ]


@dataclass(frozen=True)
class ViolationDepth:
    first_hankel_size: int | None
    detected: bool
    checked_through: int
    epistemic_status: str = "EXACT_FINITE_ADVERSARIAL_MODEL_ONLY"
    proves_rh: bool = False


def first_exact_stieltjes_violation(
    inverse_moments: list[Fraction], max_hankel_size: int
) -> ViolationDepth:
    """Find the first finite exact Stieltjes PSD failure in supplied moments."""

    if not isinstance(max_hankel_size, int) or max_hankel_size < 1:
        raise ValueError("max_hankel_size must be positive")
    checked = 0
    for size in range(1, max_hankel_size + 1):
        if len(inverse_moments) < 2 * size:
            break
        cert = exact_stieltjes_certificate(inverse_moments, hankel_size=size)
        checked = size
        if not cert.finite_positive:
            return ViolationDepth(size, True, checked)
    return ViolationDepth(None, False, checked)
