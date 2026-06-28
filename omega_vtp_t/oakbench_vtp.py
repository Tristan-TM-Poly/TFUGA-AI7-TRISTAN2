"""OAKBench helpers for Ω-VTP-T++.

These routines are intentionally small and explicit. They are not a replacement
for full benchmark suites; they provide first-pass falsification and regression
checks for TensorProd-Lift experiments.
"""

from __future__ import annotations

from typing import Callable, Dict

import numpy as np

from .tensor_prod_lift import benchmark_lift, fit_linear_operator, tensor_prod_lift


def oak_polynomial_exactness_demo() -> Dict[str, float | str]:
    """Verify exact representation of a bounded-degree polynomial.

    F(x, y) = 3x^2 + 5xy - 7y^3 + 2 should be exactly representable in a
    degree-3 monomial lift, up to floating-point roundoff.
    """

    rng = np.random.default_rng(123)
    x = rng.normal(size=(256, 2))
    y_true = 3 * x[:, 0] ** 2 + 5 * x[:, 0] * x[:, 1] - 7 * x[:, 1] ** 3 + 2

    phi = tensor_prod_lift(x, degree=3)
    coeffs = np.zeros(phi.features.shape[1])
    coeff_map = {
        (0, 0): 2.0,
        (2, 0): 3.0,
        (1, 1): 5.0,
        (0, 3): -7.0,
    }
    for idx, alpha in enumerate(phi.alphas):
        coeffs[idx] = coeff_map.get(alpha, 0.0)

    y_pred = phi.features @ coeffs
    err = y_true - y_pred
    relative = float(np.linalg.norm(err) / max(np.linalg.norm(y_true), np.finfo(float).eps))

    return {
        "case": "degree_3_polynomial_exactness",
        "relative_residual": relative,
        "max_abs_error": float(np.max(np.abs(err))),
        "oak_status": "certified" if relative < 1e-12 else "failed",
    }


def oak_dynamic_lift_demo(
    dynamics: Callable[[np.ndarray], np.ndarray] | None = None,
    *,
    degree: int = 4,
    sample_count: int = 512,
) -> Dict[str, float | int | str]:
    """Fit z_{t+1} ≈ A z_t for a simple polynomial map.

    Default map:
        x_{t+1} = 0.7x + 0.1x^2

    The lifted system is truncated to `degree`, so the residual is the OAK truth
    signal: high residual means the chosen feature space is not closed enough.
    """

    if dynamics is None:
        dynamics = lambda x: 0.7 * x + 0.1 * x**2  # noqa: E731

    x = np.linspace(-1.0, 1.0, sample_count).reshape(-1, 1)
    y = dynamics(x)

    z_x = tensor_prod_lift(x, degree=degree).features
    z_y = tensor_prod_lift(y, degree=degree).features

    fit = fit_linear_operator(z_x, z_y, certify_tol=1e-8)

    return {
        "case": "polynomial_dynamic_lift",
        "degree": degree,
        "sample_count": sample_count,
        "feature_count": fit.report.feature_count,
        "relative_residual": fit.report.relative_residual,
        "max_abs_error": fit.report.max_abs_error,
        "condition_number": fit.report.condition_number,
        "rank": fit.report.rank,
        "oak_status": fit.report.oak_status,
    }


def oak_speed_memory_demo() -> Dict[str, float | int | str]:
    """Benchmark a moderate lift and return speed/memory data."""

    rng = np.random.default_rng(456)
    samples = rng.normal(size=(1024, 8))
    return benchmark_lift(samples, degree=3, basis="monomial", repeats=3)
