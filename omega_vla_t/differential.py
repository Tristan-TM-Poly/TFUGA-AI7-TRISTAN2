"""Differential linear algebra for Ω-VLA-T∞.

Finite-difference operators are deterministic numerical approximations.  They
must not be confused with symbolic derivatives or proof of differentiability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.float64]
VectorFunction = Callable[[Array], npt.ArrayLike]
ScalarFunction = Callable[[Array], float]


def _point(value: npt.ArrayLike) -> Array:
    point = np.asarray(value, dtype=float)
    if point.ndim != 1 or not np.all(np.isfinite(point)):
        raise ValueError("point must be a finite one-dimensional array")
    return point


def _step_vector(step: float | npt.ArrayLike, dimension: int) -> Array:
    if np.isscalar(step):
        steps = np.full(dimension, float(step))
    else:
        steps = np.asarray(step, dtype=float)
    if steps.shape != (dimension,) or np.any(steps <= 0) or not np.all(np.isfinite(steps)):
        raise ValueError("step must contain one positive finite value per coordinate")
    return steps


def directional_derivative(
    function: ScalarFunction,
    point: npt.ArrayLike,
    direction: npt.ArrayLike,
    *,
    step: float = 1e-6,
    normalize: bool = False,
) -> float:
    x = _point(point)
    vector = _point(direction)
    if vector.shape != x.shape:
        raise ValueError("direction must have the same dimension as point")
    if step <= 0:
        raise ValueError("step must be positive")
    if normalize:
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise ValueError("cannot normalize the zero direction")
        vector = vector / norm
    forward = float(function(x + step * vector))
    backward = float(function(x - step * vector))
    if not np.isfinite(forward) or not np.isfinite(backward):
        raise ValueError("function returned a non-finite value")
    return (forward - backward) / (2.0 * step)


def jacobian(
    function: VectorFunction,
    point: npt.ArrayLike,
    *,
    step: float | npt.ArrayLike = 1e-6,
) -> Array:
    x = _point(point)
    steps = _step_vector(step, x.size)
    center = np.asarray(function(x), dtype=float)
    if center.ndim == 0:
        center = center.reshape(1)
    if center.ndim != 1 or not np.all(np.isfinite(center)):
        raise ValueError("function must return a finite scalar or one-dimensional array")

    result = np.empty((center.size, x.size), dtype=float)
    for index, delta in enumerate(steps):
        offset = np.zeros_like(x)
        offset[index] = delta
        forward = np.asarray(function(x + offset), dtype=float).reshape(-1)
        backward = np.asarray(function(x - offset), dtype=float).reshape(-1)
        if forward.shape != center.shape or backward.shape != center.shape:
            raise ValueError("function output dimension changed near the evaluation point")
        result[:, index] = (forward - backward) / (2.0 * delta)
    return result


def gradient_fd(
    function: ScalarFunction,
    point: npt.ArrayLike,
    *,
    step: float | npt.ArrayLike = 1e-6,
) -> Array:
    return jacobian(lambda x: np.array([function(x)], dtype=float), point, step=step)[0]


def hessian(
    function: ScalarFunction,
    point: npt.ArrayLike,
    *,
    step: float | npt.ArrayLike = 1e-4,
    symmetrize: bool = True,
) -> Array:
    x = _point(point)
    steps = _step_vector(step, x.size)
    value = float(function(x))
    if not np.isfinite(value):
        raise ValueError("function returned a non-finite value")

    result = np.empty((x.size, x.size), dtype=float)
    for i in range(x.size):
        ei = np.zeros_like(x)
        ei[i] = steps[i]
        result[i, i] = (
            float(function(x + ei)) - 2.0 * value + float(function(x - ei))
        ) / (steps[i] ** 2)
        for j in range(i + 1, x.size):
            ej = np.zeros_like(x)
            ej[j] = steps[j]
            mixed = (
                float(function(x + ei + ej))
                - float(function(x + ei - ej))
                - float(function(x - ei + ej))
                + float(function(x - ei - ej))
            ) / (4.0 * steps[i] * steps[j])
            result[i, j] = mixed
            result[j, i] = mixed

    if symmetrize:
        result = 0.5 * (result + result.T)
    if not np.all(np.isfinite(result)):
        raise ValueError("non-finite Hessian approximation")
    return result


def propagate_covariance(jacobian_matrix: npt.ArrayLike, covariance: npt.ArrayLike) -> Array:
    """First-order covariance propagation Σ_y ≈ J Σ_x Jᵀ."""
    matrix = np.asarray(jacobian_matrix, dtype=float)
    sigma = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or sigma.ndim != 2:
        raise ValueError("jacobian and covariance must be matrices")
    if sigma.shape != (matrix.shape[1], matrix.shape[1]):
        raise ValueError("covariance shape must match the Jacobian input dimension")
    if not np.allclose(sigma, sigma.T, atol=1e-12, rtol=0.0):
        raise ValueError("covariance must be symmetric")
    if np.min(np.linalg.eigvalsh(sigma)) < -1e-12:
        raise ValueError("covariance must be positive semidefinite")
    result = matrix @ sigma @ matrix.T
    return 0.5 * (result + result.T)


@dataclass(frozen=True)
class LinearizationReport:
    point: Array
    value: Array
    jacobian: Array
    perturbation: Array
    predicted_value: Array
    observed_value: Array
    residual: Array
    absolute_error: float
    relative_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "point": self.point.tolist(),
            "value": self.value.tolist(),
            "jacobian": self.jacobian.tolist(),
            "perturbation": self.perturbation.tolist(),
            "predicted_value": self.predicted_value.tolist(),
            "observed_value": self.observed_value.tolist(),
            "residual": self.residual.tolist(),
            "absolute_error": self.absolute_error,
            "relative_error": self.relative_error,
        }


def audit_linearization(
    function: VectorFunction,
    point: npt.ArrayLike,
    perturbation: npt.ArrayLike,
    *,
    step: float | npt.ArrayLike = 1e-6,
) -> LinearizationReport:
    x = _point(point)
    delta = _point(perturbation)
    if delta.shape != x.shape:
        raise ValueError("perturbation must match the point dimension")
    value = np.asarray(function(x), dtype=float).reshape(-1)
    derivative = jacobian(function, x, step=step)
    predicted = value + derivative @ delta
    observed = np.asarray(function(x + delta), dtype=float).reshape(-1)
    if observed.shape != value.shape:
        raise ValueError("function output dimension changed at perturbed point")
    residual = observed - predicted
    absolute = float(np.linalg.norm(residual))
    scale = max(float(np.linalg.norm(observed)), np.finfo(float).eps)
    return LinearizationReport(
        point=x,
        value=value,
        jacobian=derivative,
        perturbation=delta,
        predicted_value=predicted,
        observed_value=observed,
        residual=residual,
        absolute_error=absolute,
        relative_error=absolute / scale,
    )
