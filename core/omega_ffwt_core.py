#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Omega FFWT Core

A minimal, executable, numpy-only Fast Fractal Wavelet Transform core.

This is not the final mathematical FFWT canon. It is the first guarded
implementation layer: an adaptive Haar-fractal multiscale transform that exposes
the exact objects needed by Ω-FFWT-HAC-CVCD-ASP-MAX:

- approximation coefficients
- detail coefficients per level
- energy by scale
- entropy/sparsity
- persistence and fractal energy ratios
- inter-scale coherence
- reconstruction for OAK error checks

The design principle is OAK-safe: every hyper/FFWT signature remains grounded in
real-valued energy, reconstruction, stability, and benchmarkable invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple
import math

import numpy as np


@dataclass(frozen=True)
class FFWTNode:
    level: int
    start: int
    length: int
    energy: float
    detail_energy: float
    residual_energy: float
    should_refine: bool


def _as_float_array(signal: np.ndarray) -> np.ndarray:
    x = np.asarray(signal, dtype=float).copy()
    if x.ndim != 1:
        raise ValueError("omega_ffwt_core currently expects a 1D signal")
    if x.size < 4:
        raise ValueError("signal must contain at least 4 samples")
    return x


def _haar_step(x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if x.size % 2 == 1:
        x = x[:-1]
    approximation = (x[0::2] + x[1::2]) / math.sqrt(2.0)
    detail = (x[0::2] - x[1::2]) / math.sqrt(2.0)
    return approximation, detail


def _inverse_haar_step(approximation: np.ndarray, detail: np.ndarray) -> np.ndarray:
    x0 = (approximation + detail) / math.sqrt(2.0)
    x1 = (approximation - detail) / math.sqrt(2.0)
    out = np.empty(approximation.size * 2, dtype=float)
    out[0::2] = x0
    out[1::2] = x1
    return out


def haar_fractal_transform(
    signal: np.ndarray,
    max_levels: int | None = None,
    energy_threshold: float = 1e-10,
    adaptive: bool = True,
) -> Dict[str, Any]:
    """Compute a guarded adaptive Haar-fractal transform.

    Parameters
    ----------
    signal:
        1D real signal.
    max_levels:
        Maximum dyadic depth. Defaults to floor(log2(n))-1.
    energy_threshold:
        Relative threshold used for adaptive refinement.
    adaptive:
        If true, stop when detail energy becomes negligible. The full dyadic
        chain is still deterministic and reconstructible.

    Returns
    -------
    dict with keys:
        original_length, working_length, approximation, details, nodes,
        energy_by_level, total_energy.
    """
    original = _as_float_array(signal)
    n0 = int(original.size)
    if max_levels is None:
        max_levels = max(1, int(math.floor(math.log2(n0))) - 1)

    # Work on an even dyadic-compatible prefix for simple reconstruction.
    working_length = 2 ** int(math.floor(math.log2(n0)))
    x = original[:working_length].copy()
    total_energy = float(np.sum(x * x) + 1e-30)

    details: Dict[int, np.ndarray] = {}
    energy_by_level: Dict[int, float] = {}
    nodes: List[FFWTNode] = []
    current = x

    for level in range(1, max_levels + 1):
        if current.size < 4:
            break
        approximation, detail = _haar_step(current)
        detail_energy = float(np.sum(detail * detail))
        residual_energy = float(np.sum(approximation * approximation))
        relative_detail = detail_energy / total_energy
        should_refine = (not adaptive) or (relative_detail >= energy_threshold) or level <= 2

        details[level] = detail
        energy_by_level[level] = detail_energy
        nodes.append(FFWTNode(
            level=level,
            start=0,
            length=int(current.size),
            energy=float(np.sum(current * current)),
            detail_energy=detail_energy,
            residual_energy=residual_energy,
            should_refine=bool(should_refine),
        ))
        current = approximation
        if adaptive and not should_refine and level >= 3:
            break

    return {
        "original_length": n0,
        "working_length": working_length,
        "approximation": current,
        "details": details,
        "nodes": [node.__dict__ for node in nodes],
        "energy_by_level": energy_by_level,
        "total_energy": total_energy,
        "residual_energy": float(np.sum(current * current)),
        "energy_threshold": float(energy_threshold),
        "adaptive": bool(adaptive),
    }


def inverse_haar_fractal_transform(coeffs: Dict[str, Any]) -> np.ndarray:
    """Reconstruct the dyadic working prefix from transform coefficients."""
    x = np.asarray(coeffs["approximation"], dtype=float)
    details = coeffs["details"]
    for level in sorted(details.keys(), reverse=True):
        detail = np.asarray(details[level], dtype=float)
        if detail.size != x.size:
            # Adaptive truncation can end at unequal sizes if a user mutates coeffs.
            m = min(detail.size, x.size)
            x = x[:m]
            detail = detail[:m]
        x = _inverse_haar_step(x, detail)
    return x


def normalized_entropy(values: Iterable[float]) -> float:
    arr = np.asarray([max(float(v), 0.0) for v in values], dtype=float)
    total = float(np.sum(arr))
    if total <= 0.0 or arr.size <= 1:
        return 0.0
    p = arr / total
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / math.log(arr.size))


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = min(a.size, b.size)
    if m < 3:
        return 0.0
    a = a[:m] - float(np.mean(a[:m]))
    b = b[:m] - float(np.mean(b[:m]))
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-30:
        return 0.0
    return float(np.dot(a, b) / denom)


def extract_ffwt_signatures(coeffs: Dict[str, Any]) -> Dict[str, float]:
    """Extract OAK-safe multiscale FFWT signatures."""
    details: Dict[int, np.ndarray] = coeffs.get("details", {})
    energy_by_level: Dict[int, float] = {int(k): float(v) for k, v in coeffs.get("energy_by_level", {}).items()}
    total_energy = float(coeffs.get("total_energy", 0.0) + 1e-30)
    residual_energy = float(coeffs.get("residual_energy", 0.0))

    sig: Dict[str, float] = {}
    for level in sorted(energy_by_level):
        sig[f"ffwt_detail_energy_L{level}"] = energy_by_level[level]
        sig[f"ffwt_relative_energy_L{level}"] = energy_by_level[level] / total_energy

    ordered_levels = sorted(energy_by_level)
    energies = np.asarray([energy_by_level[level] for level in ordered_levels], dtype=float)
    sig["ffwt_total_detail_energy"] = float(np.sum(energies))
    sig["ffwt_total_energy"] = total_energy
    sig["ffwt_residual_energy"] = residual_energy
    sig["ffwt_residual_ratio"] = residual_energy / total_energy
    sig["ffwt_energy_entropy"] = normalized_entropy(energies)
    sig["ffwt_active_levels"] = float(len(ordered_levels))

    if energies.size:
        dominant_idx = int(np.argmax(energies))
        dominant_level = int(ordered_levels[dominant_idx])
        sig["ffwt_dominant_level"] = float(dominant_level)
        sig["ffwt_dominant_relative_energy"] = float(energies[dominant_idx] / total_energy)
        shallow = float(np.sum(energies[: max(1, min(2, energies.size))]))
        deep = float(np.sum(energies[max(0, energies.size // 2):]))
        sig["fractal_ratio"] = deep / (shallow + 1e-30)
        # Energy decay slope in log2 scale.
        x = np.asarray(ordered_levels, dtype=float)
        y = np.log(energies + 1e-30)
        if x.size >= 2:
            slope, _ = np.polyfit(x, y, 1)
            sig["ffwt_log_energy_slope"] = float(slope)
        else:
            sig["ffwt_log_energy_slope"] = 0.0
    else:
        sig["ffwt_dominant_level"] = 0.0
        sig["ffwt_dominant_relative_energy"] = 0.0
        sig["fractal_ratio"] = 0.0
        sig["ffwt_log_energy_slope"] = 0.0

    # Inter-scale coherence/correlation between adjacent detail levels.
    coherences: List[float] = []
    for a_level, b_level in zip(ordered_levels[:-1], ordered_levels[1:]):
        corr = _safe_corr(details[a_level], details[b_level])
        coh = corr * corr
        sig[f"ffwt_coherence_L{a_level}_L{b_level}"] = float(coh)
        coherences.append(float(coh))
    sig["ffwt_mean_adjacent_coherence"] = float(np.mean(coherences)) if coherences else 0.0

    # Reconstruction check for OAK sanity.
    try:
        recon = inverse_haar_fractal_transform(coeffs)
        sig["ffwt_reconstruction_energy"] = float(np.sum(recon * recon))
        sig["ffwt_reconstruction_energy_error"] = abs(sig["ffwt_reconstruction_energy"] - total_energy) / total_energy
    except Exception:
        sig["ffwt_reconstruction_energy"] = 0.0
        sig["ffwt_reconstruction_energy_error"] = 1.0

    return sig


def ffwt_signature(signal: np.ndarray, max_levels: int | None = None) -> Dict[str, float]:
    """Convenience one-shot transform + signature extraction."""
    coeffs = haar_fractal_transform(signal, max_levels=max_levels)
    return extract_ffwt_signatures(coeffs)
