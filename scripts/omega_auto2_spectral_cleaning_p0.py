#!/usr/bin/env python3
"""Omega AUTO2 P0 spectral cleaning algorithms.

Offline, deterministic reference implementation for the next spectral cleaning
P0 batch:

- spike_removal_core_algorithm_v1
- baseline_correction_core_algorithm_v1
- noise_estimation_core_algorithm_v1

This module processes synthetic spectra only. It performs no network calls and
makes no scientific, medical, regulatory, or commercial claim.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from datetime import datetime, timezone
from statistics import median
from typing import Any

from scripts.omega_auto2_spectral_core_p0 import validate_spectrum_schema

EXTERNAL_ACTIONS_ALLOWED = False
PRODUCTION_USE_ALLOWED = False
CUSTOMER_DATA_ALLOWED = False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finite_float_list(values: Any) -> list[float]:
    if not isinstance(values, list):
        return []
    out: list[float] = []
    for value in values:
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
            out.append(float(value))
    return out


def estimate_noise(intensity: list[float]) -> dict[str, Any]:
    """Estimate local noise using first-difference median absolute deviation."""
    if len(intensity) < 3:
        return {
            "ok": False,
            "noise_level": 0.0,
            "warnings": ["noise_requires_at_least_three_points"],
        }
    diffs = [intensity[i + 1] - intensity[i] for i in range(len(intensity) - 1)]
    med = median(diffs)
    abs_dev = [abs(diff - med) for diff in diffs]
    mad = median(abs_dev)
    noise_level = 1.4826 * mad
    return {
        "ok": True,
        "noise_level": float(noise_level),
        "warnings": ["noise_level_zero_or_flat_signal"] if noise_level == 0 else [],
    }


def remove_spikes(intensity: list[float], threshold: float = 5.0) -> dict[str, Any]:
    """Replace isolated high residual points with neighbor interpolation."""
    if len(intensity) < 3:
        return {
            "cleaned": list(intensity),
            "spike_indices": [],
            "warnings": ["spike_removal_requires_at_least_three_points"],
        }

    noise = estimate_noise(intensity)
    noise_level = float(noise["noise_level"])
    cleaned = list(intensity)
    spike_indices: list[int] = []

    if noise_level <= 0:
        return {
            "cleaned": cleaned,
            "spike_indices": spike_indices,
            "warnings": noise["warnings"],
        }

    for index in range(1, len(intensity) - 1):
        neighbor_estimate = 0.5 * (intensity[index - 1] + intensity[index + 1])
        residual = abs(intensity[index] - neighbor_estimate)
        if residual > threshold * noise_level:
            cleaned[index] = neighbor_estimate
            spike_indices.append(index)

    return {
        "cleaned": cleaned,
        "spike_indices": spike_indices,
        "warnings": [],
    }


def estimate_linear_baseline(axis: list[float], intensity: list[float]) -> dict[str, Any]:
    """Estimate a simple endpoint linear baseline."""
    if len(axis) != len(intensity) or len(axis) < 2:
        return {
            "ok": False,
            "baseline": [],
            "corrected": [],
            "warnings": ["baseline_requires_matching_axis_and_intensity"],
        }
    x0, x1 = axis[0], axis[-1]
    y0, y1 = intensity[0], intensity[-1]
    if x1 == x0:
        return {
            "ok": False,
            "baseline": [],
            "corrected": [],
            "warnings": ["baseline_requires_nonzero_axis_range"],
        }
    slope = (y1 - y0) / (x1 - x0)
    baseline = [y0 + slope * (x - x0) for x in axis]
    corrected = [y - b for y, b in zip(intensity, baseline)]
    return {
        "ok": True,
        "baseline": baseline,
        "corrected": corrected,
        "warnings": [],
    }


def clean_spectrum(spectrum: dict[str, Any], spike_threshold: float = 5.0) -> dict[str, Any]:
    """Run synthetic P0 spectral cleaning and return an OAK-style report."""
    schema = validate_spectrum_schema(spectrum)
    if not schema["ok"]:
        return {
            "status": "FAIL",
            "errors": schema["errors"],
            "warnings": schema["warnings"],
            "result": {},
            "residue_report": {
                "error_count": len(schema["errors"]),
                "warning_count": len(schema["warnings"]),
                "spike_count": 0,
            },
            "external_actions_allowed": EXTERNAL_ACTIONS_ALLOWED,
            "production_use_allowed": PRODUCTION_USE_ALLOWED,
            "customer_data_allowed": CUSTOMER_DATA_ALLOWED,
            "next_action": "fix_spectrum_fixture",
            "generated_at": now_iso(),
        }

    axis = _finite_float_list(spectrum.get("axis"))
    intensity = _finite_float_list(spectrum.get("intensity"))
    spike_report = remove_spikes(intensity, threshold=spike_threshold)
    baseline_report = estimate_linear_baseline(axis, spike_report["cleaned"])
    noise_report = estimate_noise(intensity)

    warnings = list(schema["warnings"])
    warnings.extend(spike_report.get("warnings", []))
    warnings.extend(baseline_report.get("warnings", []))
    warnings.extend(noise_report.get("warnings", []))

    errors: list[str] = [] if baseline_report["ok"] else ["baseline_estimation_failed"]
    status = "PASS" if not errors else "FAIL"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "result": {
            "spectrum_id": spectrum.get("spectrum_id"),
            "axis": axis,
            "spike_removed_intensity": spike_report["cleaned"],
            "spike_indices": spike_report["spike_indices"],
            "baseline": baseline_report["baseline"],
            "baseline_corrected_intensity": baseline_report["corrected"],
            "noise_level": noise_report["noise_level"],
        },
        "residue_report": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "spike_count": len(spike_report["spike_indices"]),
            "noise_level": noise_report["noise_level"],
        },
        "external_actions_allowed": EXTERNAL_ACTIONS_ALLOWED,
        "production_use_allowed": PRODUCTION_USE_ALLOWED,
        "customer_data_allowed": CUSTOMER_DATA_ALLOWED,
        "next_action": "ready_for_oakbench_p0" if status == "PASS" else "fix_cleaning_residues",
        "generated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", help="Path to a synthetic spectrum JSON fixture")
    parser.add_argument("--spike-threshold", type=float, default=5.0)
    args = parser.parse_args()
    spectrum = json.loads(pathlib.Path(args.fixture).read_text(encoding="utf-8"))
    print(json.dumps(clean_spectrum(spectrum, spike_threshold=args.spike_threshold), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
