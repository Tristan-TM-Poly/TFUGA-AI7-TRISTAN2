#!/usr/bin/env python3
"""Independent Lagrange-Bürmann coefficient oracle for Ω-INVERSE-T∞.

For F(h)=a1*h+a2*h^2+... with a1 != 0 and inverse H(z),

    [z^n] H(z) = (1/n) [h^(n-1)] (h/F(h))^n.

This module intentionally reuses only low-level exact series arithmetic from the
reference compiler and does not call either reversion implementation. It is a
third coefficient oracle for OAK cross-validation.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from omega_inverse_compiler import (
    classify_invertibility,
    pad,
    series_pow,
    series_reciprocal,
)


def revert_series_lagrange(coeffs: Sequence, order: int) -> list[Fraction]:
    """Return inverse coefficients through ``order`` by Lagrange-Bürmann."""
    if order < 1:
        raise ValueError("order must be >= 1")
    forward = pad(coeffs, order)
    status, _ = classify_invertibility(forward)
    if status != "regular":
        raise ValueError("Lagrange-Bürmann Taylor reversion requires a[1] != 0")

    # F(h)/h = a1 + a2*h + ... .  Therefore h/F(h) is the reciprocal
    # of this shifted coefficient series and has a nonzero constant term.
    f_over_h = forward[1:]
    phi = series_reciprocal(f_over_h, max(0, order - 1))

    inverse = [Fraction(0)] * (order + 1)
    for n in range(1, order + 1):
        coefficient = series_pow(phi, n, n - 1)[n - 1]
        inverse[n] = coefficient / n
    return inverse


def cross_validate_three_engines(coeffs: Sequence, order: int) -> dict:
    """Compare triangular, formal-Newton and Lagrange-Bürmann engines exactly."""
    from omega_inverse_compiler import revert_series, revert_series_newton

    triangular = revert_series(coeffs, order)
    newton = revert_series_newton(coeffs, order)
    lagrange = revert_series_lagrange(coeffs, order)
    return {
        "order": order,
        "all_equal": triangular == newton == lagrange,
        "triangular_equals_newton": triangular == newton,
        "triangular_equals_lagrange": triangular == lagrange,
        "newton_equals_lagrange": newton == lagrange,
        "coefficients": [str(value) for value in triangular],
    }


if __name__ == "__main__":
    examples = {
        "quadratic": [0, 1, 1],
        "exp-minus-one-order-6": [0, 1, Fraction(1, 2), Fraction(1, 6), Fraction(1, 24), Fraction(1, 120), Fraction(1, 720)],
    }
    for name, coeffs in examples.items():
        report = cross_validate_three_engines(coeffs, 6)
        print(name, report)
