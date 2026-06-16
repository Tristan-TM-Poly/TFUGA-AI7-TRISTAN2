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
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import sys

import numpy as np

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from omega_ffwt_core import extract_ffwt_signatures, haar_fractal_transform  # noqa: E402


def _flatten_numeric(raw_data: np.ndarray) -> np.ndarray:
    signal = np.asarray(raw_data, dtype=float).reshape(-1)
    if signal.size < 4:
        raise ValueError("jkd_fusion_strike requires at least 4 numeric samples")
    signal = signal - float(np.mean(signal))
    std = float(np.std(signal))
    if std > 1e-12:
        signal = signal / std
    return signal


def _signature(signal: np.ndarray) -> Dict[str, float]:
    coeffs = haar_fractal_transform(signal, max_levels=8, adaptive=True)
    return extract_ffwt_signatures(coeffs)


def _base_score(signatures: Dict[str, float]) -> float:
    coherence = float(signatures.get("ffwt_mean_adjacent_coherence", 0.0))
    entropy = float(signatures.get("ffwt_energy_entropy", 1.0))
    dominant = float(signatures.get("ffwt_dominant_relative_energy", 0.0))
    residual_error = float(signatures.get("ffwt_reconstruction_energy_error", 1.0))
    structure = 0.45 * coherence + 0.35 * dominant + 0.20 * max(0.0, 1.0 - entropy)
    score = 100.0 * structure * max(0.0, 1.0 - min(1.0, residual_error))
    return float(np.clip(score, 0.0, 100.0))


def _permutation_control(signal: np.ndarray, reference_score: float, n: int, seed: int) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(max(1, n)):
        shuffled = np.array(signal, copy=True)
        rng.shuffle(shuffled)
        scores.append(_base_score(_signature(shuffled)))
    null_mean = float(np.mean(scores))
    null_std = float(np.std(scores) + 1e-12)
    z_score = float((reference_score - null_mean) / null_std)
    percentile = float(np.mean(np.asarray(scores) <= reference_score))
    return {
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
        disagreement reduces score.
    permutation_checks:
        Number of shuffled null samples. This prevents random flattened data from
        being canonized just because it has nonzero multiscale energy.
    seed:
        Deterministic seed for null controls.
    """
    signal = _flatten_numeric(raw_data)
    signatures = _signature(signal)
    score = _base_score(signatures)

    control = _permutation_control(signal, score, permutation_checks, seed)
    percentile = control["null_percentile"]

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
