"""Formal-series bridge: central xi derivatives -> Theta coefficients -> moments.

No RH assumption is needed for the algebraic conversion itself. Under RH, the
resulting alternating log-derivative coefficients have the interpretation
p_k = sum gamma_n^(-2k).
"""

from __future__ import annotations

from math import factorial
from typing import Sequence, TypeVar, List

T = TypeVar("T")


def normalized_theta_coeffs_from_xi_even_derivatives(
    even_derivatives: Sequence[T],
) -> List[T]:
    """Convert [xi, xi'', xi^(4), ...] at 1/2 to normalized Theta coefficients.

    If d_m = xi^(2m)(1/2), then

        Theta(u)/Theta(0) = sum_{m>=0} a_m u^m,
        a_m = d_m / ((2m)! d_0).

    The first returned coefficient is exactly 1 (in the input numeric type when
    possible). This is a formal identity; it does not assume RH.
    """

    if not even_derivatives:
        raise ValueError("at least xi(1/2) is required")
    d0 = even_derivatives[0]
    if d0 == 0:
        raise ValueError("xi(1/2) must be nonzero")
    out = []
    for m, derivative in enumerate(even_derivatives):
        out.append(derivative / (factorial(2 * m) * d0))
    return out


def log_derivative_coefficients(normalized_coeffs: Sequence[T]) -> List[T]:
    """Return q_n for A'(u)/A(u)=sum q_n u^n from A(u)=sum a_n u^n.

    Requires a_0=1. With N+1 supplied A coefficients, N log-derivative
    coefficients are returned. The recurrence is exact in exact arithmetic:

        q_n = (n+1)a_{n+1} - sum_{j=1}^n a_j q_{n-j}.
    """

    if not normalized_coeffs:
        raise ValueError("normalized_coeffs must be non-empty")
    a0 = normalized_coeffs[0]
    if a0 != 1:
        raise ValueError("normalized_coeffs[0] must equal 1")
    q: List[T] = []
    for n in range(len(normalized_coeffs) - 1):
        value = (n + 1) * normalized_coeffs[n + 1]
        for j in range(1, n + 1):
            value -= normalized_coeffs[j] * q[n - j]
        q.append(value)
    return q


def inverse_moments_from_theta_coeffs(normalized_coeffs: Sequence[T]) -> List[T]:
    """Return formal p_k from normalized Theta coefficients.

    The convention is

        A'(u)/A(u) = p_1 - p_2 u + p_3 u^2 - ...

    so p_{n+1}=(-1)^n q_n. Under RH these equal positive inverse-even zero
    moments. Without RH they remain formal coefficients and need not be positive.
    """

    q = log_derivative_coefficients(normalized_coeffs)
    return [value if n % 2 == 0 else -value for n, value in enumerate(q)]


def inverse_moments_from_xi_even_derivatives(even_derivatives: Sequence[T]) -> List[T]:
    """Direct composition of central derivatives -> normalized Theta -> p_k."""

    return inverse_moments_from_theta_coeffs(
        normalized_theta_coeffs_from_xi_even_derivatives(even_derivatives)
    )
