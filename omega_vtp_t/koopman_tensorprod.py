"""Koopman-style operators built from TensorProd observables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .bases import chebyshev_lift
from .closure_residual import ClosureReport, closure_residual
from .tensor_prod_lift import Alpha, LiftResult, LinearOperatorFit, fit_linear_operator, tensor_prod_lift


@dataclass(frozen=True)
class KoopmanTensorProdFit:
    operator: np.ndarray
    fit: LinearOperatorFit
    degree: int
    basis: str
    alphas: tuple[Alpha, ...]
    closure: ClosureReport


def _resolve_lift(lift: str | Callable[..., LiftResult]) -> Callable[..., LiftResult]:
    if callable(lift):
        return lift
    if lift == "monomial":
        return tensor_prod_lift
    if lift == "chebyshev":
        return chebyshev_lift
    raise ValueError("lift must be 'monomial', 'chebyshev', or a callable.")


def fit_koopman_tensorprod(
    x_samples: Sequence[Sequence[float]] | np.ndarray,
    y_samples: Sequence[Sequence[float]] | np.ndarray,
    *,
    degree: int,
    lift: str | Callable[..., LiftResult] = "monomial",
    certify_tol: float = 1e-10,
) -> KoopmanTensorProdFit:
    """Fit lifted_y approximately equal to K lifted_x."""

    lift_fn = _resolve_lift(lift)
    x_lift = lift_fn(x_samples, degree)
    y_lift = lift_fn(y_samples, degree)
    fit = fit_linear_operator(x_lift.features, y_lift.features, certify_tol=certify_tol)
    closure = closure_residual(x_samples, y_samples, degree=degree, lift_fn=lift_fn)
    return KoopmanTensorProdFit(
        operator=fit.operator,
        fit=fit,
        degree=degree,
        basis=x_lift.basis,
        alphas=x_lift.alphas,
        closure=closure,
    )


def predict_lifted(fit: KoopmanTensorProdFit, x_samples: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    """Predict lifted coordinates from x using the fitted operator."""

    lift_fn = _resolve_lift(fit.basis)
    z = lift_fn(x_samples, fit.degree).features
    return z @ fit.operator.T
