"""Anomaly utilities for Ω-TRANSFORM-T."""

from __future__ import annotations

from typing import Any

import numpy as np

from .ffwt import fractal_fertility_weights
from .fwt import haar_fwt_1d
from .metrics import robust_zscore


def fertility_anomaly_scores(x, levels: int | None = None) -> dict[str, Any]:
    """Project multi-scale fertility weights back to sample-space anomaly scores.

    The result is a lightweight interpretable proxy, not a certified detector.
    """
    x = np.asarray(x, dtype=float).ravel()
    coeffs = haar_fwt_1d(x, levels=levels)
    weights = fractal_fertility_weights(coeffs)

    padded_len = int(coeffs["padded_len"])
    score = np.zeros(padded_len, dtype=float)

    for level_index, w in enumerate(weights):
        level = level_index + 1
        block = 2**level
        for k, value in enumerate(np.asarray(w, dtype=float).ravel()):
            start = k * block
            stop = min((k + 1) * block, padded_len)
            score[start:stop] += max(0.0, float(value) - 1.0)

    score = score[: x.size]
    z = robust_zscore(score)
    return {
        "scores": score,
        "robust_zscores": z,
        "max_score": float(np.max(score)) if score.size else 0.0,
        "max_abs_robust_zscore": float(np.max(np.abs(z))) if z.size else 0.0,
        "oak_warning": "Fertility anomaly score is exploratory and must be benchmarked.",
    }
