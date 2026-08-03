"""FFWT-T: heuristic Fast Fractal Wavelet Transform prototype.

Definition:
    FFWT(X) = FWT(X) + fractal fertility weights + CVCD/OAK reports.

The MVP uses Haar FWT and computes heuristic fertility weights from coefficient
amplitude, inter-scale persistence, and a local roughness proxy.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .fwt import coeff_energy, haar_fwt_1d, haar_ifwt_1d, threshold_coeffs


def _normalize01(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return np.array([], dtype=float)
    mn = float(np.min(x))
    mx = float(np.max(x))
    if mx - mn < eps:
        return np.zeros_like(x, dtype=float)
    return (x - mn) / (mx - mn + eps)


def _resample_to(x: np.ndarray, n: int) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    if n <= 0:
        return np.array([], dtype=float)
    if x.size == n:
        return x.copy()
    if x.size == 0:
        return np.zeros(n, dtype=float)
    xp = np.linspace(0.0, 1.0, x.size)
    xnew = np.linspace(0.0, 1.0, n)
    return np.interp(xnew, xp, x)


def _local_roughness_proxy(detail: np.ndarray) -> np.ndarray:
    d = np.asarray(detail, dtype=float).ravel()
    if d.size <= 2:
        return np.zeros_like(d)
    return _normalize01(np.abs(np.gradient(d)))


def fractal_fertility_weights(
    coeffs: dict[str, Any],
    amplitude_power: float = 1.0,
    persistence_weight: float = 0.75,
    roughness_weight: float = 0.25,
) -> list[np.ndarray]:
    """Return one fertility weight array per detail level."""
    details = [np.asarray(d, dtype=float) for d in coeffs["details"]]
    abs_details = [_normalize01(np.abs(d)) for d in details]
    weights: list[np.ndarray] = []

    for i, amp in enumerate(abs_details):
        n = amp.size
        persistence_parts = []
        if i > 0:
            persistence_parts.append(_resample_to(abs_details[i - 1], n))
        if i + 1 < len(abs_details):
            persistence_parts.append(_resample_to(abs_details[i + 1], n))
        persistence = np.mean(np.vstack(persistence_parts), axis=0) if persistence_parts else np.zeros(n)
        roughness = _local_roughness_proxy(details[i])
        w = 1.0 + np.power(amp, amplitude_power) + persistence_weight * persistence + roughness_weight * roughness
        weights.append(w.astype(float))

    return weights


def ffwt_1d(
    x,
    levels: int | None = None,
    keep_fraction: float | None = None,
    fertility_threshold: float | None = None,
    normalize_weighted_energy: bool = True,
) -> dict[str, Any]:
    """Compute FFWT-T coefficients for a 1D signal."""
    base = haar_fwt_1d(x, levels=levels)
    weights = fractal_fertility_weights(base)

    weighted_details = []
    for d, w in zip(base["details"], weights):
        wd = np.asarray(d, dtype=float) * w
        if normalize_weighted_energy:
            original_energy = np.sqrt(np.sum(np.asarray(d) ** 2)) + 1e-12
            weighted_energy = np.sqrt(np.sum(wd ** 2)) + 1e-12
            wd = wd * (original_energy / weighted_energy)
        if fertility_threshold is not None:
            wd = np.where(w >= float(fertility_threshold), wd, 0.0)
        weighted_details.append(wd)

    ff = {
        **base,
        "details": weighted_details,
        "base_details": base["details"],
        "fractal_weights": weights,
        "transform": "FFWT-T/Haar-fractal-heuristic",
    }

    if keep_fraction is not None:
        ff = threshold_coeffs(ff, keep_fraction=keep_fraction, mode="hard")

    return ff


def iffw_transform_1d(ffwt_coeffs: dict[str, Any], trim: bool = True) -> np.ndarray:
    """Reconstruct from the currently stored FFWT coefficient representation."""
    return haar_ifwt_1d(ffwt_coeffs, trim=trim)


def fractal_fertility_report(ffwt_coeffs: dict[str, Any]) -> dict[str, Any]:
    weights = ffwt_coeffs.get("fractal_weights", [])
    detail_scores = []
    for i, w in enumerate(weights):
        w = np.asarray(w, dtype=float)
        detail_scores.append(
            {
                "level": i + 1,
                "mean_weight": float(np.mean(w)) if w.size else 0.0,
                "max_weight": float(np.max(w)) if w.size else 0.0,
                "min_weight": float(np.min(w)) if w.size else 0.0,
                "active_fraction_weight_gt_1_5": float(np.mean(w > 1.5)) if w.size else 0.0,
            }
        )

    return {
        "transform": ffwt_coeffs.get("transform", "unknown"),
        "levels": ffwt_coeffs.get("levels"),
        "fertility_by_level": detail_scores,
        "energy": coeff_energy(ffwt_coeffs),
    }
