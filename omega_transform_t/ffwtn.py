"""FFWT-N-T prototype.

N means N-dimensional, N-variable, N-recursive, N-node, and nonlinear-residue-aware.
This MVP implements practical recursive 1D and multichannel coherence pieces.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .ffwt import ffwt_1d
from .fwt import flatten_coeffs


def recursive_ffwt_1d(x, depth: int = 2, levels: int | None = None) -> dict[str, Any]:
    """Apply FFWT recursively to flattened coefficient embeddings."""
    depth = max(1, int(depth))
    stages: list[dict[str, Any]] = []
    current = np.asarray(x, dtype=float).ravel()

    for _ in range(depth):
        coeffs = ffwt_1d(current, levels=levels)
        stages.append(coeffs)
        current = flatten_coeffs(coeffs)

    return {
        "transform": "FFWT-N-recursive",
        "depth": depth,
        "stages": stages,
        "final_embedding": current,
    }


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    n = min(a.size, b.size)
    if n <= 1:
        return 0.0
    a = a[:n]
    b = b[:n]
    sa = float(np.std(a))
    sb = float(np.std(b))
    if sa < 1e-12 or sb < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def multichannel_ffwt_coherence(X, levels: int | None = None) -> dict[str, Any]:
    """Compute FFWT per channel and a coefficient-space coherence matrix."""
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[None, :]
    channels = X.shape[0]

    coeffs = [ffwt_1d(X[c], levels=levels) for c in range(channels)]
    embeddings = [flatten_coeffs(c) for c in coeffs]

    coh = np.eye(channels, dtype=float)
    for i in range(channels):
        for j in range(i + 1, channels):
            cij = _safe_corr(embeddings[i], embeddings[j])
            coh[i, j] = coh[j, i] = cij

    return {
        "transform": "FFWT-N-multichannel-coherence",
        "channels": channels,
        "coeffs": coeffs,
        "coherence_matrix": coh,
        "mean_abs_offdiag_coherence": float(np.mean(np.abs(coh[np.triu_indices(channels, k=1)]))) if channels > 1 else 0.0,
    }


def ffwtn(X, mode: str = "auto", depth: int = 1, levels: int | None = None) -> dict[str, Any]:
    """General FFWT-N entrypoint for 1D vectors and 2D channel-by-sample matrices."""
    arr = np.asarray(X, dtype=float)
    if arr.ndim == 1:
        return recursive_ffwt_1d(arr, depth=depth, levels=levels)
    if arr.ndim == 2:
        return multichannel_ffwt_coherence(arr, levels=levels)
    return {
        "transform": "FFWT-N-flattened-tensor-fallback",
        "original_shape": arr.shape,
        "result": recursive_ffwt_1d(arr.ravel(), depth=depth, levels=levels),
        "oak_warning": "Higher-dimensional separable transforms are not implemented in this MVP; tensor was flattened.",
    }
