"""OAK metrics for Ω-TRANSFORM-T."""

from __future__ import annotations

import numpy as np


def relative_l2_error(x, xhat) -> float:
    x = np.asarray(x, dtype=float).ravel()
    xhat = np.asarray(xhat, dtype=float).ravel()[: x.size]
    return float(np.linalg.norm(x - xhat) / (np.linalg.norm(x) + 1e-12))


def snr_db(clean, estimate) -> float:
    clean = np.asarray(clean, dtype=float).ravel()
    estimate = np.asarray(estimate, dtype=float).ravel()[: clean.size]
    noise = clean - estimate
    signal_power = float(np.mean(clean**2)) + 1e-12
    noise_power = float(np.mean(noise**2)) + 1e-12
    return float(10.0 * np.log10(signal_power / noise_power))


def energy_ratio(x, y) -> float:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    return float((np.sum(y**2) + 1e-12) / (np.sum(x**2) + 1e-12))


def robust_zscore(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) + 1e-12
    return 0.67448975 * (x - med) / mad


def topk_overlap(pred_scores, truth_mask, k: int) -> float:
    scores = np.asarray(pred_scores, dtype=float).ravel()
    truth = np.asarray(truth_mask, dtype=bool).ravel()
    n = min(scores.size, truth.size)
    if n == 0:
        return 0.0
    scores = scores[:n]
    truth = truth[:n]
    k = max(1, min(int(k), n))
    idx = np.argpartition(scores, n - k)[n - k:]
    return float(np.mean(truth[idx]))
