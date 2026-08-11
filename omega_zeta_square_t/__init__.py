"""Ω-ZETA-SQUARE-T∞ — centered-square research primitives for Riemann zeta.

This package is a research/verification toolkit. It does not claim a proof of RH.
"""

from .certificates import (
    ExactPSDReport,
    ExactStieltjesCertificate,
    exact_determinant,
    exact_hankel_matrix,
    exact_principal_minors,
    exact_psd_report,
    exact_stieltjes_certificate,
    leading_only_false_positive_hankel,
)
from .core import (
    SquareCoordinate,
    centered_square,
    decode_square,
    height_squared,
    in_centered_critical_strip,
    nontrivial_zero_image,
    rh_defect,
    strip_boundary,
    trivial_zero_image,
)
from .jacobi import (
    JacobiRecurrence,
    jacobi_characteristic_polynomial,
    jacobi_recurrence_from_inverse_moments,
)
from .moments import (
    finite_stieltjes_report,
    hankel_matrix,
    inverse_even_moments,
    ldlt_psd,
    leading_principal_minors,
)
from .oak import ClaimStatus, OakClaim, validate_claim
from .pade import (
    PadeApproximant,
    pade_from_series,
    stieltjes_pade_from_inverse_moments,
    stieltjes_series_from_inverse_moments,
)
from .proof_graph import load_and_validate_proof_graph, validate_proof_graph
from .series import (
    inverse_moments_from_theta_coeffs,
    inverse_moments_from_xi_even_derivatives,
    log_derivative_coefficients,
    normalized_theta_coeffs_from_xi_even_derivatives,
)

__all__ = [
    "SquareCoordinate",
    "centered_square",
    "decode_square",
    "height_squared",
    "in_centered_critical_strip",
    "nontrivial_zero_image",
    "rh_defect",
    "strip_boundary",
    "trivial_zero_image",
    "inverse_even_moments",
    "hankel_matrix",
    "ldlt_psd",
    "leading_principal_minors",
    "finite_stieltjes_report",
    "ExactPSDReport",
    "ExactStieltjesCertificate",
    "exact_determinant",
    "exact_hankel_matrix",
    "exact_principal_minors",
    "exact_psd_report",
    "exact_stieltjes_certificate",
    "leading_only_false_positive_hankel",
    "PadeApproximant",
    "pade_from_series",
    "stieltjes_series_from_inverse_moments",
    "stieltjes_pade_from_inverse_moments",
    "JacobiRecurrence",
    "jacobi_recurrence_from_inverse_moments",
    "jacobi_characteristic_polynomial",
    "ClaimStatus",
    "OakClaim",
    "validate_claim",
    "normalized_theta_coeffs_from_xi_even_derivatives",
    "log_derivative_coefficients",
    "inverse_moments_from_theta_coeffs",
    "inverse_moments_from_xi_even_derivatives",
    "validate_proof_graph",
    "load_and_validate_proof_graph",
]
