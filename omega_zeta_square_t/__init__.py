"""Ω-ZETA-SQUARE-T∞ — centered-square research primitives for Riemann zeta.

This package is a research/verification toolkit. It does not claim a proof of RH.
"""

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
from .moments import (
    finite_stieltjes_report,
    hankel_matrix,
    inverse_even_moments,
    leading_principal_minors,
)
from .oak import ClaimStatus, OakClaim, validate_claim

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
    "leading_principal_minors",
    "finite_stieltjes_report",
    "ClaimStatus",
    "OakClaim",
    "validate_claim",
]
