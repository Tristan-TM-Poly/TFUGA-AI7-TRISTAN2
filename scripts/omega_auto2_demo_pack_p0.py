#!/usr/bin/env python3
"""Omega AUTO2 P0 demo pack generator.

Creates an offline synthetic before/after report from the integrated AUTO2 P0
spine. The report is a demo artifact only: no production use, no customer data,
no billing, and no scientific/regulatory claim.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from omega_auto2_p0 import run_p0_pipeline

DEFAULT_DEMO_REQUEST = pathlib.Path("fixtures/omega_auto2/demo_pack/demo_request.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _round_list(values: Any, digits: int = 6) -> list[float]:
    if not isinstance(values, list):
        return []
    rounded: list[float] = []
    for value in values:
        if isinstance(value, (int, float)):
            rounded.append(round(float(value), digits))
    return rounded


def generate_demo_report(request: dict[str, Any]) -> dict[str, Any]:
    """Generate a stable, synthetic before/after demo report."""
    pipeline_report = run_p0_pipeline(request)
    payload = request.get("payload", {}) if isinstance(request, dict) else {}
    cleaning = pipeline_report.get("spectral_cleaning", {})
    result = cleaning.get("result", {}) if isinstance(cleaning, dict) else {}

    raw_intensity = _round_list(payload.get("intensity", [])) if isinstance(payload, dict) else []
    cleaned_intensity = _round_list(result.get("spike_removed_intensity", []))
    baseline = _round_list(result.get("baseline", []))
    baseline_corrected = _round_list(result.get("baseline_corrected_intensity", []))
    spike_indices = list(result.get("spike_indices", [])) if isinstance(result.get("spike_indices", []), list) else []

    return {
        "demo_id": "omega_auto2_demo_pack_p0",
        "oak_status": pipeline_report.get("oak_status", "FAIL"),
        "request_id": request.get("request_id") if isinstance(request, dict) else None,
        "spectrum_id": payload.get("spectrum_id") if isinstance(payload, dict) else None,
        "summary": {
            "input_points": len(raw_intensity),
            "spike_count": len(spike_indices),
            "noise_level": result.get("noise_level"),
            "pipeline_next_action": pipeline_report.get("next_action"),
            "demo_next_action": "ready_for_review_pack_p0" if pipeline_report.get("oak_status") == "PASS" else "fix_demo_residues",
        },
        "before_after": {
            "axis": _round_list(payload.get("axis", [])) if isinstance(payload, dict) else [],
            "raw_intensity": raw_intensity,
            "spike_removed_intensity": cleaned_intensity,
            "baseline": baseline,
            "baseline_corrected_intensity": baseline_corrected,
            "spike_indices": spike_indices,
        },
        "module_statuses": pipeline_report.get("module_statuses", {}),
        "residue_report": pipeline_report.get("residue_report", {}),
        "oak_disclaimer": {
            "synthetic_only": True,
            "external_actions_allowed": False,
            "production_use_allowed": False,
            "customer_data_allowed": False,
            "scientific_or_regulatory_claim": False,
            "commercial_claim": False,
        },
        "generated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", default=str(DEFAULT_DEMO_REQUEST))
    parser.add_argument("--output")
    args = parser.parse_args()
    report = generate_demo_report(load_json(pathlib.Path(args.request)))
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["oak_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
