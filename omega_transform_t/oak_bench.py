"""OAKBench for Ω-TRANSFORM-T.

Benchmarks are intentionally simple and transparent.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .ffwt import ffwt_1d, iffw_transform_1d
from .fwt import flatten_coeffs, haar_fwt_1d, haar_ifwt_1d, threshold_coeffs


def relative_error(x, xhat) -> float:
    x = np.asarray(x, dtype=float).ravel()
    xhat = np.asarray(xhat, dtype=float).ravel()[: x.size]
    denom = float(np.linalg.norm(x)) + 1e-12
    return float(np.linalg.norm(x - xhat) / denom)


def sparse_retention_fraction(coeffs: dict[str, Any]) -> float:
    flat = flatten_coeffs(coeffs)
    if flat.size == 0:
        return 0.0
    return float(np.mean(np.abs(flat) > 1e-12))


def oak_report(x, coeffs: dict[str, Any], xhat) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).ravel()
    xhat = np.asarray(xhat, dtype=float).ravel()[: x.size]
    residual = x - xhat
    retention = sparse_retention_fraction(coeffs)
    compression_ratio = float(1.0 / max(retention, 1e-12))
    return {
        "relative_reconstruction_error": relative_error(x, xhat),
        "sparse_retention_fraction": retention,
        "compression_ratio_estimate": compression_ratio,
        "residual_energy": float(np.sum(residual**2)),
        "signal_energy": float(np.sum(x**2)),
        "oak_status": "measured_not_proven",
    }


def compare_fwt_ffwt_thresholding(x, levels: int | None = None, keep_fraction: float = 0.2) -> dict[str, Any]:
    """Compare FWT and FFWT at the same sparse keep fraction."""
    x = np.asarray(x, dtype=float).ravel()

    fwt = haar_fwt_1d(x, levels=levels)
    fwt_sparse = threshold_coeffs(fwt, keep_fraction=keep_fraction)
    xhat_fwt = haar_ifwt_1d(fwt_sparse)
    report_fwt = oak_report(x, fwt_sparse, xhat_fwt)

    ffwt = ffwt_1d(x, levels=levels, keep_fraction=keep_fraction)
    xhat_ffwt = iffw_transform_1d(ffwt)
    report_ffwt = oak_report(x, ffwt, xhat_ffwt)

    delta = report_fwt["relative_reconstruction_error"] - report_ffwt["relative_reconstruction_error"]
    if delta > 1e-9:
        verdict = "FFWT better on reconstruction error at same keep_fraction"
    elif delta < -1e-9:
        verdict = "FWT better on reconstruction error at same keep_fraction"
    else:
        verdict = "Tie within tolerance"

    return {
        "keep_fraction": float(keep_fraction),
        "fwt": report_fwt,
        "ffwt": report_ffwt,
        "delta_error_fwt_minus_ffwt": float(delta),
        "verdict": verdict,
        "oak_warning": "One synthetic/one-signal result is not a general proof.",
    }
