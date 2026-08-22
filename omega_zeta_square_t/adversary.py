"""Exact local/finite adversary models for off-critical-line zero images.

For a centered-square zero image u=(delta+i gamma)^2 define lambda=-1/u.
Under RH delta=0 and lambda is positive real. An off-line functional/conjugate
quartet becomes a non-real conjugate pair lambda, conjugate(lambda) in the
square quotient.

The identities below are exact for isolated/finite atomic models. They are not
theorems about the full infinite Riemann zero set until the infinite tail is
controlled rigorously or the all-orders Stieltjes bridge is proved.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import prod
from typing import Iterable, Sequence

from .certificates import exact_stieltjes_certificate

Rational = int | Fraction
PairInput = tuple[Rational, Rational]


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
    critical line. This is a local pair identity, not a full-RH certificate.
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

    return finite_atomic_inverse_moments(
        positive_real_lambdas, [(pair_a, pair_b)], max_k
    )


def finite_atomic_inverse_moments(
    positive_real_lambdas: Iterable[Rational],
    conjugate_pairs: Iterable[PairInput],
    max_k: int,
) -> list[Fraction]:
    """Exact moments for positive real atoms plus non-real conjugate pairs."""

    if not isinstance(max_k, int) or max_k < 1:
        raise ValueError("max_k must be positive")
    reals = tuple(_q(value) for value in positive_real_lambdas)
    if any(value <= 0 for value in reals):
        raise ValueError("background lambda atoms must be positive")
    pairs = tuple((_q(a), _q(b)) for a, b in conjugate_pairs)
    if any(b == 0 for _, b in pairs):
        raise ValueError("conjugate-pair imaginary part must be nonzero")
    values = [sum(value**k for value in reals) for k in range(1, max_k + 1)]
    for a, b in pairs:
        pair = conjugate_pair_inverse_moments(a, b, max_k)
        values = [x + y for x, y in zip(values, pair)]
    return values


def _validated_distinct_positive_atoms(values: Iterable[Rational]) -> tuple[Fraction, ...]:
    reals = tuple(_q(value) for value in values)
    if any(value <= 0 for value in reals):
        raise ValueError("background lambda atoms must be positive")
    if len(set(reals)) != len(reals):
        raise ValueError("finite support atoms must be distinct; encode multiplicity as weights in a future extension")
    return reals


def one_pair_full_hankel_determinant(
    positive_real_lambdas: Iterable[Rational],
    pair_a: Rational,
    pair_b: Rational,
    *,
    shift: int = 0,
) -> Fraction:
    """Exact full-support Hankel determinant for one non-real conjugate pair.

    For q distinct positive real atoms r_j and pair a±ib, N=q+2 and

      det H_N^(0) = -4 b^2(a^2+b^2) Πr_j
                    Π_{i<j}(r_j-r_i)^2
                    Π_j((a-r_j)^2+b^2)^2.

    H_N^(shift) differs by (Π support atoms)^shift. Therefore every shift has
    negative determinant when b != 0. This is a finite atomic theorem only.
    """

    if not isinstance(shift, int) or shift < 0:
        raise ValueError("shift must be a non-negative integer")
    reals = _validated_distinct_positive_atoms(positive_real_lambdas)
    a_q, b_q = _q(pair_a), _q(pair_b)
    pair_norm = a_q * a_q + b_q * b_q
    base = -4 * b_q * b_q * pair_norm
    base *= prod(reals, start=Fraction(1))
    for i in range(len(reals)):
        for j in range(i + 1, len(reals)):
            base *= (reals[j] - reals[i]) ** 2
    for value in reals:
        base *= ((a_q - value) ** 2 + b_q * b_q) ** 2
    support_product = pair_norm * prod(reals, start=Fraction(1))
    return base * (support_product ** shift)


@dataclass(frozen=True)
class OnePairFiniteCertificate:
    support_size: int
    hankel_shift: int
    determinant: Fraction
    guaranteed_negative: bool
    epistemic_status: str = "PROVED_FINITE_ONE_CONJUGATE_PAIR_ATOMIC_IDENTITY"
    finite_atomic_model_only: bool = True
    proves_rh: bool = False


def one_pair_full_hankel_certificate(
    positive_real_lambdas: Iterable[Rational],
    pair_a: Rational,
    pair_b: Rational,
    *,
    shift: int = 0,
) -> OnePairFiniteCertificate:
    reals = _validated_distinct_positive_atoms(positive_real_lambdas)
    determinant = one_pair_full_hankel_determinant(reals, pair_a, pair_b, shift=shift)
    return OnePairFiniteCertificate(
        support_size=len(reals) + 2,
        hankel_shift=shift,
        determinant=determinant,
        guaranteed_negative=determinant < 0,
    )


@dataclass(frozen=True)
class FiniteInertiaCertificate:
    positive_real_atoms: int
    conjugate_pairs: int
    support_size: int
    positive_directions: int
    negative_directions: int
    zero_directions: int
    determinant_sign: int
    finite_atomic_model_only: bool = True
    epistemic_status: str = "PROVED_FINITE_ATOMIC_INERTIA_BY_REAL_EVALUATION_CONGRUENCE"
    proves_rh: bool = False


def finite_atomic_inertia_certificate(
    positive_real_atoms: int, conjugate_pairs: int
) -> FiniteInertiaCertificate:
    """Return the exact inertia predicted by the finite evaluation theorem.

    For q distinct positive real support atoms and m distinct non-real conjugate
    pairs, the full-support real Hankel quadratic form is congruent to q positive
    1x1 blocks and m blocks 2[[a,-b],[-b,-a]], each of inertia (1,1).
    """

    if not isinstance(positive_real_atoms, int) or positive_real_atoms < 0:
        raise ValueError("positive_real_atoms must be a non-negative integer")
    if not isinstance(conjugate_pairs, int) or conjugate_pairs < 0:
        raise ValueError("conjugate_pairs must be a non-negative integer")
    q, m = positive_real_atoms, conjugate_pairs
    sign = -1 if m % 2 else 1
    return FiniteInertiaCertificate(
        positive_real_atoms=q,
        conjugate_pairs=m,
        support_size=q + 2 * m,
        positive_directions=q + m,
        negative_directions=m,
        zero_directions=0,
        determinant_sign=sign,
    )


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
