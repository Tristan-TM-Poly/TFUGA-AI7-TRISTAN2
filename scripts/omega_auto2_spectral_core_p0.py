#!/usr/bin/env python3
"""Omega AUTO2 P0 spectral core validators.

Offline, deterministic reference implementation for issues #127-#128:

- axis_validation_core_algorithm_v1
- schema_validation_core_algorithm_v1

This module validates synthetic spectrum envelopes only. It performs no network
calls and makes no scientific, medical, regulatory, or commercial claim.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from datetime import datetime, timezone
from typing import Any

REQUIRED_SPECTRUM_FIELDS = [
    "spectrum_id",
    "axis",
    "intensity",
    "metadata",
]

ALLOWED_AXIS_UNITS = {"nm", "cm^-1", "ev", "hz", "index"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_axis(axis: Any, unit: str | None = None) -> dict[str, Any]:
    """Validate a numeric spectral axis."""
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {}

    if not isinstance(axis, list):
        return {
            "ok": False,
            "errors": ["axis_must_be_list"],
            "warnings": warnings,
            "summary": summary,
        }

    if len(axis) < 2:
        errors.append("axis_must_have_at_least_two_points")

    numeric_values: list[float] = []
    for index, value in enumerate(axis):
        if not _is_number(value):
            errors.append(f"axis_value_not_finite_number:{index}")
        else:
            numeric_values.append(float(value))

    if unit is None or unit == "":
        warnings.append("axis_unit_missing")
    elif unit not in ALLOWED_AXIS_UNITS:
        errors.append(f"unsupported_axis_unit:{unit}")

    if not errors and len(numeric_values) >= 2:
        diffs = [numeric_values[i + 1] - numeric_values[i] for i in range(len(numeric_values) - 1)]
        if any(diff == 0 for diff in diffs):
            errors.append("axis_contains_duplicate_neighbors")
        increasing = all(diff > 0 for diff in diffs)
        decreasing = all(diff < 0 for diff in diffs)
        if not (increasing or decreasing):
            errors.append("axis_not_monotonic")
        spacing = [abs(diff) for diff in diffs]
        min_spacing = min(spacing)
        max_spacing = max(spacing)
        if min_spacing == 0:
            errors.append("axis_zero_spacing")
        elif max_spacing / min_spacing > 10:
            warnings.append("axis_spacing_highly_irregular")
        summary = {
            "points": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "direction": "increasing" if increasing else ("decreasing" if decreasing else "mixed"),
            "min_spacing": min_spacing,
            "max_spacing": max_spacing,
        }

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def validate_spectrum_schema(spectrum: Any) -> dict[str, Any]:
    """Validate the minimal Omega SPECTRA synthetic spectrum schema."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(spectrum, dict):
        return {
            "ok": False,
            "errors": ["spectrum_must_be_object"],
            "warnings": warnings,
            "axis": {"ok": False, "errors": ["axis_not_checked"], "warnings": [], "summary": {}},
        }

    for field in REQUIRED_SPECTRUM_FIELDS:
        if field not in spectrum:
            errors.append(f"missing_required_field:{field}")

    metadata = spectrum.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata_must_be_object")
        metadata = {}
    elif metadata is None:
        metadata = {}

    axis = spectrum.get("axis")
    intensity = spectrum.get("intensity")
    unit = metadata.get("axis_unit") if isinstance(metadata, dict) else None
    axis_report = validate_axis(axis, unit=unit)

    if not axis_report["ok"]:
        errors.extend(axis_report["errors"])
    warnings.extend(axis_report["warnings"])

    if not isinstance(intensity, list):
        errors.append("intensity_must_be_list")
    else:
        for index, value in enumerate(intensity):
            if not _is_number(value):
                errors.append(f"intensity_value_not_finite_number:{index}")
        if isinstance(axis, list) and len(axis) != len(intensity):
            errors.append("axis_intensity_length_mismatch")

    if not spectrum.get("spectrum_id"):
        errors.append("spectrum_id_empty")

    if metadata.get("source") != "synthetic_fixture":
        warnings.append("metadata_source_not_synthetic_fixture")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "axis": axis_report,
    }


def oak_report(spectrum: Any) -> dict[str, Any]:
    schema = validate_spectrum_schema(spectrum)
    status = "PASS" if schema["ok"] else "FAIL"
    return {
        "status": status,
        "schema": schema,
        "external_actions_allowed": False,
        "production_use_allowed": False,
        "residue_report": {
            "error_count": len(schema["errors"]),
            "warning_count": len(schema["warnings"]),
        },
        "next_action": "ready_for_next_p0_card" if schema["ok"] else "fix_spectrum_fixture",
        "generated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", help="Path to a synthetic spectrum JSON fixture")
    args = parser.parse_args()
    spectrum = json.loads(pathlib.Path(args.fixture).read_text(encoding="utf-8"))
    print(json.dumps(oak_report(spectrum), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
