#!/usr/bin/env python3
"""Omega AUTO2 P0 usage events core.

Offline, deterministic reference implementation for issues #125-#126.

This module records synthetic usage-event envelopes only. It does not charge,
invoice, contact customers, call external services, or process private data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

REQUIRED_EVENT_FIELDS = [
    "event_id",
    "request_id",
    "namespace",
    "operation",
    "unit_type",
    "units",
    "timestamp",
    "oak_context",
]

ALLOWED_UNIT_TYPES = {
    "request",
    "spectrum",
    "batch",
    "report",
    "test_run",
}

ALLOWED_OPERATIONS = {
    "healthcheck",
    "validate_spectrum",
    "clean_spectrum",
    "detect_drift",
    "batch_qc",
    "oak_report",
    "test_run",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_usage_event(event: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(event, dict):
        return {"ok": False, "errors": ["event_must_be_object"], "warnings": []}

    for field in REQUIRED_EVENT_FIELDS:
        if field not in event:
            errors.append(f"missing_required_field:{field}")

    if event.get("unit_type") not in ALLOWED_UNIT_TYPES and "unit_type" in event:
        errors.append(f"unsupported_unit_type:{event.get('unit_type')}")

    if event.get("operation") not in ALLOWED_OPERATIONS and "operation" in event:
        errors.append(f"unsupported_operation:{event.get('operation')}")

    units = event.get("units")
    if not isinstance(units, (int, float)):
        errors.append("units_must_be_number")
    elif units < 0:
        errors.append("units_must_be_non_negative")
    elif units == 0:
        warnings.append("zero_units")

    oak_context = event.get("oak_context") if isinstance(event.get("oak_context"), dict) else {}
    if event.get("oak_context") is not None and not isinstance(event.get("oak_context"), dict):
        errors.append("oak_context_must_be_object")

    if oak_context.get("production_use"):
        warnings.append("human_review_required:production_use")
    if oak_context.get("contains_customer_data"):
        errors.append("customer_data_not_allowed_in_p0_fixture")

    for text_field in ["event_id", "request_id", "namespace", "operation"]:
        if text_field in event and not event.get(text_field):
            errors.append(f"field_empty:{text_field}")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def normalize_usage_event(event: dict[str, Any]) -> dict[str, Any]:
    validation = validate_usage_event(event)
    if not validation["ok"]:
        return {
            "status": "error",
            "event_id": event.get("event_id") if isinstance(event, dict) else None,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "oak_status": "FAIL",
            "record": {},
            "generated_at": now_iso(),
        }

    review_required = any(warning.startswith("human_review_required") for warning in validation["warnings"])
    oak_status = "REVIEW_REQUIRED" if review_required else "PASS"
    record = {
        "event_id": event["event_id"],
        "request_id": event["request_id"],
        "namespace": event["namespace"],
        "operation": event["operation"],
        "unit_type": event["unit_type"],
        "units": float(event["units"]),
        "timestamp": event["timestamp"],
        "synthetic_only": True,
    }
    return {
        "status": "review_required" if review_required else "ok",
        "event_id": event["event_id"],
        "errors": [],
        "warnings": validation["warnings"],
        "oak_status": oak_status,
        "record": record,
        "generated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", help="Path to a synthetic usage event JSON fixture")
    args = parser.parse_args()
    event = json.loads(pathlib.Path(args.fixture).read_text(encoding="utf-8"))
    print(json.dumps(normalize_usage_event(event), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
