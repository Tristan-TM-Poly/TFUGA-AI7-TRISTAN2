"""Minimal executable core for TFUGA / SAGE-TRISTAN.

This package keeps experimental modules conservative: claims stay local,
outputs expose residues, and promotion requires OAK validation.
"""

from .omega_ffwt import (
    Coefficients,
    OAKScore,
    cvcd_summary,
    energy_concentration,
    generate_signal,
    haar_ffwt_candidate,
    inverse_haar_ffwt_candidate,
    oak_score,
    real_hac,
    reconstruction_error,
    run_minimal_benchmark,
)

__all__ = [
    "Coefficients",
    "OAKScore",
    "cvcd_summary",
    "energy_concentration",
    "generate_signal",
    "haar_ffwt_candidate",
    "inverse_haar_ffwt_candidate",
    "oak_score",
    "real_hac",
    "reconstruction_error",
    "run_minimal_benchmark",
]
