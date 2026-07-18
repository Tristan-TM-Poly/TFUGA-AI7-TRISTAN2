"""FWT-T: minimal Haar Fast Wavelet Transform.

OAK-safe:
- Haar FWT is a known orthogonal wavelet transform.
- Exact reconstruction holds when all coefficients are kept.
- Compression claims require benchmark metrics.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def _next_power_of_two(n: int) -> int:
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()


def _pad_power2(x: np.ndarray) -> tuple[np.ndarray, int]:
    x = np.asarray(x, dtype=float).ravel()
    original_len = len(x)
    n2 = _next_power_of_two(original_len)
    if n2 == original_len:
        return x.copy(), original_len
    padded = np.zeros(n2, dtype=float)
    padded[:original_len] = x
    return padded, original_len


def haar_fwt_1d(x, levels: int | None = None) -> dict[str, Any]:
    """Return Haar FWT coefficients for a 1D signal."""
    a, original_len = _pad_power2(np.asarray(x, dtype=float))
    max_levels = int(math.log2(len(a))) if len(a) > 1 else 0
    if levels is None:
        levels = max_levels
    levels = max(0, min(int(levels), max_levels))

    details: list[np.ndarray] = []
    current = a
    s2 = math.sqrt(2.0)

    for _ in range(levels):
        even = current[0::2]
        odd = current[1::2]
        approx = (even + odd) / s2
        detail = (even - odd) / s2
        details.append(detail)
        current = approx

    return {
        "approx": current,
        "details": details,
        "original_len": original_len,
        "padded_len": len(a),
        "levels": levels,
        "wavelet": "haar",
    }


def haar_ifwt_1d(coeffs: dict[str, Any], trim: bool = True) -> np.ndarray:
    """Invert Haar FWT coefficients."""
    current = np.asarray(coeffs["approx"], dtype=float)
    s2 = math.sqrt(2.0)
    for detail in reversed(coeffs["details"]):
        detail = np.asarray(detail, dtype=float)
        even = (current + detail) / s2
        odd = (current - detail) / s2
        out = np.empty(even.size + odd.size, dtype=float)
        out[0::2] = even
        out[1::2] = odd
        current = out

    if trim:
        return current[: int(coeffs["original_len"])]
    return current


def flatten_coeffs(coeffs: dict[str, Any]) -> np.ndarray:
    arrays = [np.asarray(coeffs["approx"], dtype=float)]
    arrays.extend(np.asarray(d, dtype=float) for d in coeffs["details"])
    return np.concatenate([a.ravel() for a in arrays]) if arrays else np.array([], dtype=float)


def coeff_energy(coeffs: dict[str, Any]) -> dict[str, Any]:
    approx_e = float(np.sum(np.asarray(coeffs["approx"]) ** 2))
    detail_es = [float(np.sum(np.asarray(d) ** 2)) for d in coeffs["details"]]
    return {
        "approx_energy": approx_e,
        "detail_energy": detail_es,
        "total_energy": approx_e + sum(detail_es),
    }


def threshold_coeffs(coeffs: dict[str, Any], keep_fraction: float = 0.2, mode: str = "hard") -> dict[str, Any]:
    """Keep the largest absolute coefficients as a transparent sparse baseline."""
    keep_fraction = float(np.clip(keep_fraction, 0.0, 1.0))
    arrays = [np.asarray(coeffs["approx"], dtype=float).copy()]
    arrays.extend(np.asarray(d, dtype=float).copy() for d in coeffs["details"])
    flat = np.concatenate([a.ravel() for a in arrays])
    if flat.size == 0:
        return coeffs

    k = max(1, int(round(keep_fraction * flat.size)))
    threshold = np.partition(np.abs(flat), flat.size - k)[flat.size - k]

    new_arrays = []
    for a in arrays:
        if mode == "soft":
            new_a = np.sign(a) * np.maximum(np.abs(a) - threshold, 0.0)
        else:
            new_a = np.where(np.abs(a) >= threshold, a, 0.0)
        new_arrays.append(new_a)

    return {
        **coeffs,
        "approx": new_arrays[0],
        "details": new_arrays[1:],
        "threshold": float(threshold),
        "keep_fraction": keep_fraction,
        "threshold_mode": mode,
    }
