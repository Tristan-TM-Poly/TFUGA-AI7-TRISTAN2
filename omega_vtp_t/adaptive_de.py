"""Adaptive degree selection for Ω-DE-TensorProd."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

from .de_tensorprod import PolynomialODE, build_carleman_operator, carleman_residual_on_samples
from .tensor_prod_lift import feature_count


@dataclass(frozen=True)
class AdaptiveDEStep:
    degree: int
    feature_count: int
    closure_coefficient: float
    sample_relative_residual: float
    residual_term_count: int
    cost: float
    oak_status: str


@dataclass(frozen=True)
class AdaptiveDESelection:
    best_degree: int
    steps: List[AdaptiveDEStep]
    stopped_reason: str
    oak_status: str


def select_ode_tensor_degree(
    ode: PolynomialODE,
    samples: Sequence[Sequence[float]] | np.ndarray,
    *,
    min_degree: int = 1,
    max_degree: int = 8,
    residual_tol: float = 1e-8,
    max_features: int = 10000,
    feature_penalty: float = 1e-4,
) -> AdaptiveDESelection:
    """Select a TensorProd degree for a polynomial ODE using OAK cost.

    Cost = sample_relative_residual + feature_penalty * feature_count.
    """

    if min_degree < 0:
        raise ValueError("min_degree must be >= 0")
    if max_degree < min_degree:
        raise ValueError("max_degree must be >= min_degree")

    steps: List[AdaptiveDEStep] = []
    best_step: AdaptiveDEStep | None = None
    stopped_reason = "max_degree_reached"

    for degree in range(min_degree, max_degree + 1):
        n_features = feature_count(ode.dimension, degree)
        if n_features > max_features:
            stopped_reason = "max_features_exceeded"
            break

        report = carleman_residual_on_samples(ode, samples, degree)
        op = build_carleman_operator(ode, degree)
        cost = float(report["sample_relative_residual"]) + feature_penalty * n_features
        step = AdaptiveDEStep(
            degree=degree,
            feature_count=n_features,
            closure_coefficient=float(op.closure_coefficient),
            sample_relative_residual=float(report["sample_relative_residual"]),
            residual_term_count=int(report["residual_term_count"]),
            cost=cost,
            oak_status=str(report["oak_status"]),
        )
        steps.append(step)
        if best_step is None or step.cost < best_step.cost:
            best_step = step
        if step.sample_relative_residual <= residual_tol:
            stopped_reason = "residual_tol_reached"
            break

    if best_step is None:
        raise RuntimeError("No adaptive DE step was evaluated.")

    if best_step.sample_relative_residual <= residual_tol:
        status = "checked"
    elif best_step.sample_relative_residual <= 1e-4:
        status = "experimental_good"
    else:
        status = "experimental_residual_watch"

    return AdaptiveDESelection(
        best_degree=best_step.degree,
        steps=steps,
        stopped_reason=stopped_reason,
        oak_status=status,
    )
