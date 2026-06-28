"""Ω-VTP-T++ — TensorProd-Lift de Tristan.

A small, dependency-light prototype for polynomial/tensor feature lifts that turn
bounded-degree polynomial nonlinearities into linear maps in an augmented space.

Core safety rule:
    no linearization claim without a measured residual.
"""

from .tensor_prod_lift import (
    LiftResult,
    LinearOperatorFit,
    OAKReport,
    feature_count,
    fit_linear_operator,
    multi_indices,
    one_plus_lift,
    polynomial_eval_from_lift,
    tensor_prod_lift,
)

__all__ = [
    "LiftResult",
    "LinearOperatorFit",
    "OAKReport",
    "feature_count",
    "fit_linear_operator",
    "multi_indices",
    "one_plus_lift",
    "polynomial_eval_from_lift",
    "tensor_prod_lift",
]
