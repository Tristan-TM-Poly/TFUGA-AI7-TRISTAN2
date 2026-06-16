#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: JKD Fusion Strike

A minimal direct-evaluation layer over omega_ffwt_core.

Principle
---------
Any numeric reality can be flattened into a 1D signal, then measured through the
same FFWT/CVCD signature extractor. JKD here means economy of motion, not loss of
OAK discipline: the function does not canonize arbitrary structure unless it
survives either an oracle target or a permutation/null-structure check.

Audit locks
-----------
- Reconstruction penalty uses exp(-error), never a negative multiplier.
- Permutation/null checks are bounded and adapt to tensor size.
- High-density tensors are deterministically downsampled for the null model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import math
import sys

import numpy as np

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from omega_ffwt_core import extract_ffwt_signatures, haar_fractal_transform  # noqa: E402

MAX_NULL_PERMUTATIONS = 50
NULL_DOWNSAMPLE_THRESHOLD = 4096
NULL_DOWNSAMPLE_SIZE = 4096


def _flatten_numeric(raw_data: np.ndarray) -> np.ndarray:
    signal = np.asarray(raw_data, dtype=float).reshape(-1)
    if signal.size < 4:
        raise ValueError("jkd_fusion_strike requires at least 4 numeric samples")
    signal = signal - float(np.mean(signal))
    std = float(np.std(signal))
    if std > 1e-12:
        signal = signal / std
    return signal


def _null_signal_view(signal: np.ndarray, seed: int) -> tuple[np.ndarray, bool]:
    """Return a deterministic null-control view bounded for CI runners."""
    if signal.size <= NULL_DOWNSAMPLE_THRESHOLD:
        return signal, False
    rng = np.random.default_rng(seed)
    indices = np.sort(rng.choice(signal.size, size=NULL_DOWNSAMPLE_SIZE, replace=False))
    return signal[indices], True


def _signature(signal: np.ndarray) -> Dict[str, float]:
    coeffs = haar_fractal_transform(signal, max_levels=8, adaptive=True)
    return extract_ffwt_signatures(coeffs)


def _base_score(signatures: Dict[str, float]) -> float:
    coherence = float(signatures.get("ffwt_mean_adjacent_coherence", 0.0))
    entropy = float(signatures.get("ffwt_energy_entropy", 1.0))
    dominant = float(signatures.get("ffwt_dominant_relative_energy", 0.0))
    residual_error = max(0.0, float(signatures.get("ffwt_reconstruction_energy_error", 1.0)))

    structure = 0.45 * coherence + 0.35 * dominant + 0.20 * max(0.0, 1.0 - entropy)
    reconstruction_penalty = math.exp(-residual_error)
    score = 100.0 * max(0.0, structure) * reconstruction_penalty
    return float(np.clip(score, 0.0, 100.0))


def _permutation_budget(requested: int, signal_size: int) -> int:
    requested = max(1, int(requested))
    requested = min(requested, MAX_NULL_PERMUTATIONS)
    if signal_size > 65536:
        return min(requested, 8)
    if signal_size > 16384:
        return min(requested, 12)
    if signal_size > 4096:
        return min(requested, 16)
    return requested


def _permutation_control(signal: np.ndarray, reference_score: float, n: int, seed: int) -> Dict[str, float | int | bool]:
    null_signal, downsampled = _null_signal_view(signal, seed=seed)
    budget = _permutation_budget(n, signal.size)
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(budget):
        shuffled = np.array(null_signal, copy=True)
        rng.shuffle(shuffled)
        scores.append(_base_score(_signature(shuffled)))
    null_mean = float(np.mean(scores))
    null_std = float(np.std(scores) + 1e-12)
    z_score = float((reference_score - null_mean) / null_std)
    percentile = float(np.mean(np.asarray(scores) <= reference_score))
    return {
        "requested_permutations": int(n),
        "used_permutations": int(budget),
        "downsampled": bool(downsampled),
        "null_signal_size": int(null_signal.size),
        "null_mean_score": null_mean,
        "null_std_score": null_std,
        "null_z_score": z_score,
        "null_percentile": percentile,
    }


def jkd_strike(
    raw_data: np.ndarray,
    oracle_target: Optional[float] = None,
    permutation_checks: int = 24,
    seed: int = 20260616,
) -> Dict[str, Any]:
    """Evaluate any numeric tensor through the FFWT/CVCD/OAK direct path.

    Parameters
    ----------
    raw_data:
        Any numeric vector/matrix/tensor.
    oracle_target:
        Optional expected dominant FFWT level or external target. When present,
        disagreement reduces score by exp(-relative_error).
    permutation_checks:
        Requested number of shuffled null samples. The actual number is capped by
        MAX_NULL_PERMUTATIONS and reduced for large tensors.
    seed:
        Deterministic seed for null controls.
    """
    signal = _flatten_numeric(raw_data)
    signatures = _signature(signal)
    score = _base_score(signatures)

    control = _permutation_control(signal, score, permutation_checks, seed)
    percentile = float(control["null_percentile"])

    if oracle_target is not None:
        dominant_level = float(signatures.get("ffwt_dominant_level", 0.0))
        error = abs(float(oracle_target) - dominant_level) / (abs(float(oracle_target)) + 1e-12)
        score *= float(np.exp(-error))
        oracle_error = float(error)
    else:
        oracle_error = None

    # OAK guard: without oracle, CANON requires a strong permutation separation.
    if score >= 80.0 and percentile >= 0.95:
        verdict = "CANON"
    elif score >= 40.0 and percentile >= 0.70:
        verdict = "FERTILE"
    else:
        verdict = "M_MINUS"

    return {
        "verdict": verdict,
        "oak_score": round(float(score), 4),
        "oracle_error": oracle_error,
        "shape": list(np.asarray(raw_data).shape),
        "flattened_size": int(signal.size),
        "permutation_control": control,
        "signatures_cvcd": signatures,
    }


if __name__ == "__main__":
    print("[JKD] Fusion evaluation smoke test")
    spectrum = np.array([0.1, 0.2, 0.1, 0.9, 5.0, 0.8, 0.1, 0.1], dtype=float)
    board_noise = np.random.default_rng(7).normal(size=(8, 8))
    for name, tensor in [("spectrum", spectrum), ("random_board", board_noise)]:
        result = jkd_strike(tensor)
        print(name, result["verdict"], result["oak_score"])
