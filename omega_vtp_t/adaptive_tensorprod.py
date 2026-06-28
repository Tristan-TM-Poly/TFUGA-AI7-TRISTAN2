"""Adaptive TensorProd-Lift for Ω-VTP-T++.

Start at a low degree, fit a lifted linear model, measure the OAK residual, and
increase degree only when needed. This prevents automatic explosion into huge
feature spaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Sequence

import numpy as np

from .tensor_prod_lift import LinearOperatorFit, fit_linear_operator, tensor_prod_lift


@dataclass(frozen=True)
class AdaptiveStep:
    degree: int
    feature_count: int
    relative_residual: float
    condition_number: float
    oak_status: str


@dataclass(frozen=True)
class AdaptiveLiftFit:
    best_degree: int
    best_fit: LinearOperatorFit
    steps: List[AdaptiveStep]
    stopped_reason: str


def adaptive_dynamic_lift_fit(
    x_samples: Sequence[Sequence[float]] | np.ndarray,
    dynamics: Callable[[np.ndarray], np.ndarray],
    *,
    min_degree: int = 1,
    max_degree: int = 6,
    residual_tol: float = 1e-8,
    max_features: int = 10000,
) -> AdaptiveLiftFit:
    """Fit z_{t+1} ≈ A z_t while adaptively increasing TensorProd degree.

    Args:
        x_samples: Samples x_t, shape (n_samples, n_variables).
        dynamics: Function returning x_{t+1} for each sample.
        min_degree: Starting degree.
        max_degree: Maximum degree allowed.
        residual_tol: Stop once relative residual is below this threshold.
        max_features: Stop before exceeding this many lifted features.

    Returns:
        AdaptiveLiftFit with every OAK step preserved.
    """

    if min_degree < 0:
        raise ValueError("min_degree must be >= 0.")
    if max_degree < min_degree:
        raise ValueError("max_degree must be >= min_degree.")
    if max_features < 1:
        raise ValueError("max_features must be >= 1.")

    x = np.asarray(x_samples, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if x.ndim != 2:
        raise ValueError("x_samples must be a 1D or 2D array.")

    y = np.asarray(dynamics(x), dtype=float)
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    if y.shape != x.shape:
        raise ValueError("dynamics(x_samples) must return the same shape as x_samples.")

    steps: List[AdaptiveStep] = []
    best_fit: LinearOperatorFit | None = None
    best_degree = min_degree
    best_residual = float("inf")
    stopped_reason = "max_degree_reached"

    for degree in range(min_degree, max_degree + 1):
        z_x = tensor_prod_lift(x, degree).features
        if z_x.shape[1] > max_features:
            stopped_reason = "max_features_exceeded"
            break

        z_y = tensor_prod_lift(y, degree).features
        fit = fit_linear_operator(z_x, z_y, certify_tol=residual_tol)
        residual = fit.report.relative_residual

        steps.append(
            AdaptiveStep(
                degree=degree,
                feature_count=fit.report.feature_count,
                relative_residual=residual,
                condition_number=fit.report.condition_number,
                oak_status=fit.report.oak_status,
            )
        )

        if residual < best_residual:
            best_residual = residual
            best_fit = fit
            best_degree = degree

        if residual <= residual_tol:
            stopped_reason = "residual_tol_reached"
            break

    if best_fit is None:
        raise RuntimeError("No adaptive step was run; lower min_degree or raise max_features.")

    return AdaptiveLiftFit(
        best_degree=best_degree,
        best_fit=best_fit,
        steps=steps,
        stopped_reason=stopped_reason,
    )
