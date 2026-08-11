"""Ω-ROOTFLOW-T∞ — differential geometry and continuation of polynomial zeros."""

from .continuation import ContinuationResult, ContinuationStep, continue_roots, match_roots, newton_refine
from .core import (
    RootCondition,
    basis_root_differential,
    degree_perturbation_sensitivity,
    derivative_coefficients,
    derivative_value,
    polynomial_value,
    projective_scaling_residual,
    root_conditions,
    root_differential,
    root_hessian,
    root_jacobian,
    root_velocity,
    roots,
)
from .oak import RootFlowAudit, audit_rootflow, finite_difference_root_jacobian

__all__ = [
    "ContinuationResult",
    "ContinuationStep",
    "RootCondition",
    "RootFlowAudit",
    "audit_rootflow",
    "basis_root_differential",
    "continue_roots",
    "degree_perturbation_sensitivity",
    "derivative_coefficients",
    "derivative_value",
    "finite_difference_root_jacobian",
    "match_roots",
    "newton_refine",
    "polynomial_value",
    "projective_scaling_residual",
    "root_conditions",
    "root_differential",
    "root_hessian",
    "root_jacobian",
    "root_velocity",
    "roots",
]
