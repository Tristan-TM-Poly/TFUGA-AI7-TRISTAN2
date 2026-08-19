"""Coefficient selection operators for Ω-TRANSFORM-T.

The key improvement in this module is OAK-safe separation between:

1. scoring coefficients with FFWT fertility weights;
2. reconstructing with the original, unwarped Haar coefficients.

That avoids a failure mode from the first MVP: multiplying coefficients by
heuristic weights can degrade reconstruction because the inverse transform then
receives distorted coefficients. Fertility should select first; distortion should
be an explicitly measured experiment, not the default.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .ffwt import fractal_fertility_weights
from .fwt import haar_fwt_1d


def _copy_coeffs(coeffs: dict[str, Any]) -> dict[str, Any]:
    return {
        **coeffs,
        "approx": np.asarray(coeffs["approx"], dtype=float).copy(),
        "details": [np.asarray(d, dtype=float).copy() for d in coeffs["details"]],
    }


def _flatten_score_parts(approx_score: np.ndarray, detail_scores: list[np.ndarray]) -> np.ndarray:
    arrays = [np.asarray(approx_score, dtype=float).ravel()]
    arrays.extend(np.asarray(s, dtype=float).ravel() for s in detail_scores)
    return np.concatenate(arrays) if arrays else np.array([], dtype=float)


def fertility_select_coeffs(
    x,
    levels: int | None = None,
    keep_fraction: float = 0.2,
    approx_priority: float = 1.0,
    amplitude_weight: float = 1.0,
    fertility_weight: float = 1.0,
) -> dict[str, Any]:
    """Select original Haar coefficients by a fertility-aware score.

    OAK note: this is not proof that fertility helps. It is a safer experimental
    operator because reconstruction uses original coefficients instead of
    fertility-distorted coefficients.
    """
    base = haar_fwt_1d(x, levels=levels)
    selected = _copy_coeffs(base)
    keep_fraction = float(np.clip(keep_fraction, 0.0, 1.0))

    approx = np.asarray(base["approx"], dtype=float)
    details = [np.asarray(d, dtype=float) for d in base["details"]]
    weights = fractal_fertility_weights(base)

    approx_score = approx_priority * amplitude_weight * np.abs(approx)
    detail_scores = []
    for d, w in zip(details, weights):
        amp = amplitude_weight * np.abs(d)
        fert = fertility_weight * np.asarray(w, dtype=float) * (np.abs(d) + 1e-12)
        detail_scores.append(amp + fert)

    all_scores = _flatten_score_parts(approx_score, detail_scores)
    if all_scores.size == 0:
        return selected

    k = max(1, int(round(keep_fraction * all_scores.size)))
    threshold = np.partition(all_scores, all_scores.size - k)[all_scores.size - k]

    approx_mask = approx_score >= threshold
    detail_masks = [s >= threshold for s in detail_scores]

    selected["approx"] = np.where(approx_mask, selected["approx"], 0.0)
    selected["details"] = [
        np.where(mask, detail, 0.0)
        for mask, detail in zip(detail_masks, selected["details"])
    ]

    selected["selection"] = "fertility_select_original_coefficients"
    selected["keep_fraction"] = keep_fraction
    selected["score_threshold"] = float(threshold)
    selected["fractal_weights"] = weights
    selected["approx_mask_fraction"] = float(np.mean(approx_mask)) if approx_mask.size else 0.0
    selected["detail_mask_fractions"] = [
        float(np.mean(mask)) if mask.size else 0.0 for mask in detail_masks
    ]
    return selected


def amplitude_select_coeffs(x, levels: int | None = None, keep_fraction: float = 0.2) -> dict[str, Any]:
    """Plain FWT selection baseline by absolute coefficient amplitude."""
    return fertility_select_coeffs(
        x,
        levels=levels,
        keep_fraction=keep_fraction,
        approx_priority=1.0,
        amplitude_weight=1.0,
        fertility_weight=0.0,
    )
