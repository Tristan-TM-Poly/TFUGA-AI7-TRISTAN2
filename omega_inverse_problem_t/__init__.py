"""Ω-INVERSE-PROBLEM-T∞ public API."""

from .core import (
    LinearGaussianPosterior,
    NonlinearInverseResult,
    cycle_consistency_linear,
    finite_difference_jacobian,
    gauss_newton_inverse,
    inverse_problem_report,
    least_squares,
    linear_gaussian_posterior,
    matvec,
    pseudoinverse,
    route_linear_inverse,
    singular_spectrum,
    tikhonov,
)
from .diagnostics import identifiability_geometry, penrose_residuals, resolution_matrices

__all__ = [
    "LinearGaussianPosterior",
    "NonlinearInverseResult",
    "cycle_consistency_linear",
    "finite_difference_jacobian",
    "gauss_newton_inverse",
    "identifiability_geometry",
    "inverse_problem_report",
    "least_squares",
    "linear_gaussian_posterior",
    "matvec",
    "penrose_residuals",
    "pseudoinverse",
    "resolution_matrices",
    "route_linear_inverse",
    "singular_spectrum",
    "tikhonov",
]
