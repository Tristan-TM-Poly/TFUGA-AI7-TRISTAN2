"""Ω-VTP-T++ — TensorProd-Lift de Tristan.

A small, dependency-light prototype for polynomial/tensor feature lifts that turn
bounded-degree polynomial nonlinearities into linear maps in an augmented space.

Core safety rule:
    no linearization claim without a measured residual.
"""

from .adaptive_tensorprod import AdaptiveLiftFit, AdaptiveStep, adaptive_dynamic_lift_fit
from .sparse_tensorprod import (
    SparseLiftResult,
    SparseSelectionReport,
    select_by_correlation_with_target,
    select_by_variance,
    sparse_tensor_prod_lift,
)
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
    "AdaptiveLiftFit",
    "AdaptiveStep",
    "LiftResult",
    "LinearOperatorFit",
    "OAKReport",
    "SparseLiftResult",
    "SparseSelectionReport",
    "adaptive_dynamic_lift_fit",
    "feature_count",
    "fit_linear_operator",
    "multi_indices",
    "one_plus_lift",
    "polynomial_eval_from_lift",
    "select_by_correlation_with_target",
    "select_by_variance",
    "sparse_tensor_prod_lift",
    "tensor_prod_lift",
]
