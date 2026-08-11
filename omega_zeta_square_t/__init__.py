"""Ω-ZETA-SQUARE-T∞ — centered-square research primitives for Riemann zeta.

This package is a research/verification toolkit. It does not claim a proof of RH.
"""

from .adversary import (
    OnePairFiniteCertificate,
    ViolationDepth,
    centered_pair_hankel2_determinant,
    conjugate_pair_hankel2_determinant,
    conjugate_pair_inverse_moments,
    first_exact_stieltjes_violation,
    lambda_pair_from_beta_gamma,
    mixed_inverse_moments,
    one_pair_full_hankel_certificate,
    one_pair_full_hankel_determinant,
)
from .bibliography import validate_bibliography_ledger
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
from .cvcd import MinimalSupport, cvcd_support_report, minimal_dependency_supports
from .intervals import (
    IntervalPSDReport,
    IntervalStieltjesCertificate,
    RationalInterval,
    interval_determinant,
    interval_psd_report,
    interval_stieltjes_certificate,
    inverse_moment_intervals_from_theta_coeffs,
    inverse_moment_intervals_from_xi_even_derivatives,
    normalized_theta_intervals_from_xi_even_derivatives,
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
from .obligations import ProofObligation, export_obligation_bundle, lean_stub, obligations_from_proof_graph
from .pade import (
    PadeApproximant,
    pade_from_series,
    stieltjes_pade_from_inverse_moments,
    stieltjes_series_from_inverse_moments,
)
from .proof_graph import load_and_validate_proof_graph, validate_proof_graph
from .provenance import EvidenceKind, IntervalEvidence, ProvenanceVerdict, validate_interval_evidence
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
    "RationalInterval",
    "IntervalPSDReport",
    "IntervalStieltjesCertificate",
    "normalized_theta_intervals_from_xi_even_derivatives",
    "inverse_moment_intervals_from_theta_coeffs",
    "inverse_moment_intervals_from_xi_even_derivatives",
    "interval_determinant",
    "interval_psd_report",
    "interval_stieltjes_certificate",
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
    "EvidenceKind",
    "IntervalEvidence",
    "ProvenanceVerdict",
    "validate_interval_evidence",
    "ProofObligation",
    "obligations_from_proof_graph",
    "export_obligation_bundle",
    "lean_stub",
    "MinimalSupport",
    "minimal_dependency_supports",
    "cvcd_support_report",
    "validate_bibliography_ledger",
    "ViolationDepth",
    "OnePairFiniteCertificate",
    "lambda_pair_from_beta_gamma",
    "conjugate_pair_inverse_moments",
    "conjugate_pair_hankel2_determinant",
    "centered_pair_hankel2_determinant",
    "mixed_inverse_moments",
    "first_exact_stieltjes_violation",
    "one_pair_full_hankel_determinant",
    "one_pair_full_hankel_certificate",
]
