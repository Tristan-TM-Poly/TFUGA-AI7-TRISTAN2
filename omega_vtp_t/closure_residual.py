"""Closure residuals for lifted TensorProd/Koopman spaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .conditioning import matrix_condition_number
from .tensor_prod_lift import LiftResult, fit_linear_operator, tensor_prod_lift


@dataclass(frozen=True)
class ClosureReport:
    degree: int
    basis: str
    residual_norm: float
    relative_residual: float
    closure_coefficient: float
    condition_number: float
    feature_count: int
    sample_count: int
    oak_status: str


def closure_residual(
    x_samples: Sequence[Sequence[float]] | np.ndarray,
    y_samples: Sequence[Sequence[float]] | np.ndarray,
    *,
    degree: int,
    lift_fn: Callable[..., LiftResult] = tensor_prod_lift,
) -> ClosureReport:
    """Measure whether Phi(y) is in the linear span of Phi(x)."""

    x_lift = lift_fn(x_samples, degree)
    y_lift = lift_fn(y_samples, degree)
    fit = fit_linear_operator(x_lift.features, y_lift.features)
    rel = fit.report.relative_residual
    closure = 1.0 - rel
    cond = matrix_condition_number(x_lift.features)

    return ClosureReport(
        degree=degree,
        basis=x_lift.basis,
        residual_norm=fit.report.residual_norm,
        relative_residual=rel,
        closure_coefficient=float(closure),
        condition_number=cond,
        feature_count=x_lift.features.shape[1],
        sample_count=x_lift.features.shape[0],
        oak_status=fit.report.oak_status,
    )
