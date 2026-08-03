"""Dependency-free real elliptic functions used by the Euler top.

The implementation is restricted to real ``u`` and parameter ``0 <= m <= 1``.
It uses the arithmetic-geometric mean (AGM) descending Landen transform.
"""

from __future__ import annotations

from math import asin, cos, cosh, inf, log, pi, sin, sqrt, tanh


def complete_elliptic_k(m: float, *, tolerance: float = 1e-15) -> float:
    """Return the complete elliptic integral K(m) for ``0 <= m <= 1``.

    ``m`` is the parameter (sometimes written ``k**2``), not the modulus.
    """

    if not 0.0 <= m <= 1.0:
        raise ValueError("elliptic parameter m must satisfy 0 <= m <= 1")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be positive")
    if m == 1.0:
        return inf
    if m == 0.0:
        return pi / 2.0

    a = 1.0
    b = sqrt(1.0 - m)
    while abs(a - b) > tolerance * a:
        a, b = 0.5 * (a + b), sqrt(a * b)
    return pi / (2.0 * a)


def jacobi_sncndn(u: float, m: float, *, tolerance: float = 1e-14) -> tuple[float, float, float]:
    """Return ``sn(u|m)``, ``cn(u|m)`` and ``dn(u|m)`` for real arguments.

    The limiting cases are evaluated directly:

    * ``m = 0``: ``(sin(u), cos(u), 1)``;
    * ``m = 1``: ``(tanh(u), sech(u), sech(u))``.
    """

    if not 0.0 <= m <= 1.0:
        raise ValueError("elliptic parameter m must satisfy 0 <= m <= 1")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be positive")
    if m <= tolerance:
        return sin(u), cos(u), 1.0
    if 1.0 - m <= tolerance:
        cn = 1.0 / cosh(u)
        return tanh(u), cn, cn

    a_values = [1.0]
    c_values = [sqrt(m)]
    b = sqrt(1.0 - m)

    while True:
        a_previous = a_values[-1]
        a_next = 0.5 * (a_previous + b)
        c_next = 0.5 * (a_previous - b)
        b = sqrt(a_previous * b)
        a_values.append(a_next)
        c_values.append(c_next)
        if abs(c_next) <= tolerance * a_next:
            break
        if len(a_values) > 64:
            raise ArithmeticError("AGM iteration did not converge")

    level = len(a_values) - 1
    phi = (2.0**level) * a_values[level] * u
    for index in range(level, 0, -1):
        argument = (c_values[index] / a_values[index]) * sin(phi)
        argument = max(-1.0, min(1.0, argument))
        phi = 0.5 * (phi + asin(argument))

    sn = sin(phi)
    cn = cos(phi)
    dn = sqrt(max(0.0, 1.0 - m * sn * sn))
    return sn, cn, dn


def near_separatrix_period_asymptotic(m: float) -> float:
    """Return the leading asymptotic ``K(m) ~ log(4/sqrt(1-m))``.

    This helper is diagnostic; it is not used instead of ``complete_elliptic_k``.
    """

    if not 0.0 < m < 1.0:
        raise ValueError("asymptotic requires 0 < m < 1")
    return log(4.0 / sqrt(1.0 - m))
