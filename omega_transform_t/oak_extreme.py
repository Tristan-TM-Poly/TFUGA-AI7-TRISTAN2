"""Extreme OAKBench extensions for Ω-TRANSFORM-T.

These routines add task-oriented checks while keeping the original OAKBench intact.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .anomaly import fertility_anomaly_scores
from .fwt import flatten_coeffs, haar_fwt_1d, haar_ifwt_1d, threshold_coeffs
from .metrics import relative_l2_error, snr_db, topk_overlap
from .selection import fertility_select_coeffs


def sparse_retention_fraction(coeffs: dict[str, Any]) -> float:
    flat = flatten_coeffs(coeffs)
    if flat.size == 0:
        return 0.0
    return float(np.mean(np.abs(flat) > 1e-12))


def report_sparse_reconstruction(x, coeffs: dict[str, Any]) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).ravel()
    xhat = haar_ifwt_1d(coeffs)
    residual = x - xhat[: x.size]
    retention = sparse_retention_fraction(coeffs)
    return {
        "relative_reconstruction_error": relative_l2_error(x, xhat),
        "sparse_retention_fraction": retention,
        "compression_ratio_estimate": float(1.0 / max(retention, 1e-12)),
        "residual_energy": float(np.sum(residual**2)),
        "oak_status": "measured_not_proven",
    }


def compare_amplitude_vs_fertility_selection(x, levels: int | None = None, keep_fraction: float = 0.2) -> dict[str, Any]:
    """Compare amplitude selection against fertility-aware selection.

    Both reconstruct from original Haar coefficients. This is safer than using
    weighted coefficients directly as inverse-transform input.
    """
    x = np.asarray(x, dtype=float).ravel()
    amp = threshold_coeffs(haar_fwt_1d(x, levels=levels), keep_fraction=keep_fraction)
    fert = fertility_select_coeffs(x, levels=levels, keep_fraction=keep_fraction)

    amp_report = report_sparse_reconstruction(x, amp)
    fert_report = report_sparse_reconstruction(x, fert)
    delta = amp_report["relative_reconstruction_error"] - fert_report["relative_reconstruction_error"]

    return {
        "keep_fraction": float(keep_fraction),
        "amplitude_selection": amp_report,
        "fertility_selection": fert_report,
        "delta_error_amplitude_minus_fertility": float(delta),
        "verdict": "fertility_selection_wins" if delta > 1e-9 else "amplitude_selection_wins_or_ties",
        "oak_warning": "Synthetic result only; not a global theorem.",
    }


def denoise_selection_bench(clean, noisy, levels: int | None = None, keep_fraction: float = 0.2) -> dict[str, Any]:
    """Compare sparse amplitude and fertility selection as denoisers."""
    clean = np.asarray(clean, dtype=float).ravel()
    noisy = np.asarray(noisy, dtype=float).ravel()

    amp = threshold_coeffs(haar_fwt_1d(noisy, levels=levels), keep_fraction=keep_fraction)
    fert = fertility_select_coeffs(noisy, levels=levels, keep_fraction=keep_fraction)
    amp_hat = haar_ifwt_1d(amp)
    fert_hat = haar_ifwt_1d(fert)

    return {
        "keep_fraction": float(keep_fraction),
        "input_snr_db": snr_db(clean, noisy),
        "amplitude_selection_snr_db": snr_db(clean, amp_hat),
        "fertility_selection_snr_db": snr_db(clean, fert_hat),
        "amplitude_selection_relative_error": relative_l2_error(clean, amp_hat),
        "fertility_selection_relative_error": relative_l2_error(clean, fert_hat),
        "oak_status": "measured_not_proven",
    }


def anomaly_score_bench(x, expected_mask, levels: int | None = None, top_fraction: float = 0.05) -> dict[str, Any]:
    """Evaluate fertility anomaly scores against a synthetic expected-mask."""
    x = np.asarray(x, dtype=float).ravel()
    expected = np.asarray(expected_mask, dtype=bool).ravel()[: x.size]
    scores = fertility_anomaly_scores(x, levels=levels)
    k = max(1, int(round(float(top_fraction) * x.size)))
    return {
        "top_fraction": float(top_fraction),
        "topk_expected_overlap": topk_overlap(scores["scores"], expected, k),
        "max_score": scores["max_score"],
        "max_abs_robust_zscore": scores["max_abs_robust_zscore"],
        "oak_warning": scores["oak_warning"],
        "oak_status": "measured_not_proven",
    }
