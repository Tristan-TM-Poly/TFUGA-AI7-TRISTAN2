"""Ω-VTP-T++ — TensorProd-Lift de Tristan.

A small, dependency-light prototype for polynomial/tensor feature lifts that turn
bounded-degree polynomial nonlinearities into linear maps in an augmented space.

Core safety rule:
    no linearization claim without a measured residual.
"""

from .adaptive_de import AdaptiveDESelection, AdaptiveDEStep, select_ode_tensor_degree
from .adaptive_tensorprod import AdaptiveLiftFit, AdaptiveStep, adaptive_dynamic_lift_fit
from .auxiliary_variables import (
    AuxiliaryVariableTemplate,
    exp_template,
    reciprocal_template,
    sin_cos_template,
    standard_auxiliary_templates,
)
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
from .invariant_guards import (
    InvariantCheck,
    InvariantReport,
    conservation_check,
    custom_invariant_check,
    invariant_report,
    l2_energy,
    monotone_decrease_check,
    positivity_check,
    positivity_error,
)
from .koopman_tensorprod import KoopmanTensorProdFit, fit_koopman_tensorprod, predict_lifted
from .lifted_solvers import LinearSolveReport, rk4_linear_step, solve_lifted_linear
from .low_rank_operator import LowRankOperator, compress_operator_svd
from .mminus_registry import MMinusEntry, MMinusRegistry, build_mminus_registry, entry_from_oak_status, merge_registries
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
from .residual_decomposition import ResidualComponent, ResidualDecomposition, decompose_residuals, residual_dict
from .roi_oak import (
    CostComponent,
    FinancialCase,
    RiskComponent,
    ROIOAKReport,
    ValueComponent,
    battery_revaluation_case,
    datacenter_pue_case,
    evaluate_financial_case,
    hft_risk_engine_case,
    npv,
    payback_period,
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
    "AdaptiveDESelection",
    "AdaptiveDEStep",
    "AdaptiveLiftFit",
    "AdaptiveStep",
    "AuxiliaryVariableTemplate",
    "CVCDSelection",
    "CarlemanResidualTerm",
    "CarlemanTensorProdOperator",
    "ClosureReport",
    "CostComponent",
    "FeatureFertility",
    "FinancialCase",
    "InvariantCheck",
    "InvariantReport",
    "KoopmanTensorProdFit",
    "LiftResult",
    "LinearOperatorFit",
    "LinearSolveReport",
    "LowRankOperator",
    "MMinusEntry",
    "MMinusRegistry",
    "OAKReport",
    "OAKScore",
    "PDEResidualReport",
    "PolynomialODE",
    "ROIOAKReport",
    "ResidualComponent",
    "ResidualDecomposition",
    "ResidualMetrics",
    "RiskComponent",
    "ScalingDomain",
    "SparseLiftResult",
    "SparseSelectionReport",
    "TrainTestOAKReport",
    "ValueComponent",
    "adaptive_dynamic_lift_fit",
    "battery_revaluation_case",
    "build_carleman_operator",
    "build_mminus_registry",
    "burgers_rhs_periodic",
    "carleman_residual_on_samples",
    "chebyshev_lift",
    "chebyshev_values",
    "closure_residual",
    "compress_operator_svd",
    "conservation_check",
    "custom_invariant_check",
    "datacenter_pue_case",
    "decompose_residuals",
    "entry_from_oak_status",
    "evaluate_financial_case",
    "exp_template",
    "feature_count",
    "feature_fertility_scores",
    "fit_koopman_tensorprod",
    "fit_linear_operator",
    "gradient_1d_periodic",
    "hft_risk_engine_case",
    "infer_scaling_domain",
    "invariant_report",
    "l2_energy",
    "laplacian_1d_periodic",
    "lifted_time_derivative",
    "mass",
    "matrix_condition_number",
    "merge_registries",
    "monotone_decrease_check",
    "multi_indices",
    "npv",
    "oak_score",
    "one_plus_lift",
    "payback_period",
    "pde_residual_euler",
    "periodic_boundary_residual",
    "polynomial_eval_from_lift",
    "positivity_check",
    "positivity_error",
    "predict_lifted",
    "reaction_diffusion_rhs",
    "reciprocal_template",
    "residual_dict",
    "residual_metrics",
    "rk4_linear_step",
    "scale_to_unit_interval",
    "select_by_correlation_with_target",
    "select_by_variance",
    "select_cvcd_features",
    "select_ode_tensor_degree",
    "sin_cos_template",
    "solve_lifted_linear",
    "sparse_tensor_prod_lift",
    "standard_auxiliary_templates",
    "tensor_prod_lift",
    "train_test_koopman_oak",
]
