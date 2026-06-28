"""Ω-VTP-T++ — TensorProd-Lift de Tristan.

A small, dependency-light prototype for polynomial/tensor feature lifts that turn
bounded-degree polynomial nonlinearities into linear maps in an augmented space.

Core safety rule:
    no linearization claim without a measured residual.
"""

from .adaptive_tensorprod import AdaptiveLiftFit, AdaptiveStep, adaptive_dynamic_lift_fit
from .bases import ScalingDomain, chebyshev_lift, chebyshev_values, infer_scaling_domain, scale_to_unit_interval
from .closure_residual import ClosureReport, closure_residual
from .conditioning import OAKScore, ResidualMetrics, matrix_condition_number, oak_score, residual_metrics
from .cvcd_selector import CVCDSelection, FeatureFertility, feature_fertility_scores, select_cvcd_features
from .de_tensorprod import (
    CarlemanResidualTerm,
    CarlemanTensorProdOperator,
    PolynomialODE,
    build_carleman_operator,
    carleman_residual_on_samples,
    lifted_time_derivative,
)
from .koopman_tensorprod import KoopmanTensorProdFit, fit_koopman_tensorprod, predict_lifted
from .pde_tensorprod import (
    PDEResidualReport,
    burgers_rhs_periodic,
    gradient_1d_periodic,
    laplacian_1d_periodic,
    mass,
    pde_residual_euler,
    periodic_boundary_residual,
    reaction_diffusion_rhs,
)
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
from .train_test_oak import TrainTestOAKReport, train_test_koopman_oak

__all__ = [
    "AdaptiveLiftFit",
    "AdaptiveStep",
    "CVCDSelection",
    "CarlemanResidualTerm",
    "CarlemanTensorProdOperator",
    "ClosureReport",
    "FeatureFertility",
    "KoopmanTensorProdFit",
    "LiftResult",
    "LinearOperatorFit",
    "OAKReport",
    "OAKScore",
    "PDEResidualReport",
    "PolynomialODE",
    "ResidualMetrics",
    "ScalingDomain",
    "SparseLiftResult",
    "SparseSelectionReport",
    "TrainTestOAKReport",
    "adaptive_dynamic_lift_fit",
    "build_carleman_operator",
    "burgers_rhs_periodic",
    "carleman_residual_on_samples",
    "chebyshev_lift",
    "chebyshev_values",
    "closure_residual",
    "feature_count",
    "feature_fertility_scores",
    "fit_koopman_tensorprod",
    "fit_linear_operator",
    "gradient_1d_periodic",
    "infer_scaling_domain",
    "laplacian_1d_periodic",
    "lifted_time_derivative",
    "mass",
    "matrix_condition_number",
    "multi_indices",
    "oak_score",
    "one_plus_lift",
    "pde_residual_euler",
    "periodic_boundary_residual",
    "polynomial_eval_from_lift",
    "predict_lifted",
    "reaction_diffusion_rhs",
    "residual_metrics",
    "scale_to_unit_interval",
    "select_by_correlation_with_target",
    "select_by_variance",
    "select_cvcd_features",
    "sparse_tensor_prod_lift",
    "tensor_prod_lift",
    "train_test_koopman_oak",
]
