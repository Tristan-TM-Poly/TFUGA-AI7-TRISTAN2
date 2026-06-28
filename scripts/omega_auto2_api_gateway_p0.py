#!/usr/bin/env python3
"""Omega AUTO2 P0 API gateway core.

Offline, deterministic reference implementation for issues #113-#116:

- api_gateway_input_schema_v1
- api_gateway_output_schema_v1
- api_gateway_core_algorithm_v1
- api_gateway_oak_gate_v1

This module does not call external APIs, does not activate billing, and does not
process customer data. It is a synthetic OAK-safe foundation for later PRs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any, Callable

REQUIRED_INPUT_FIELDS = [
    "request_id",
    "namespace",
    "operation",
    "payload",
    "metadata",
    "oak_context",
]

ALLOWED_OPERATIONS = {
    "healthcheck",
    "validate_spectrum",
    "clean_spectrum",
    "detect_drift",
    "batch_qc",
    "oak_report",
}

PRODUCTION_ONLY_FLAGS = {
    "production_billing",
    "external_outreach",
    "regulated_claim",
    "patent_disclosure",
    "customer_data",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_input_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimal AUTO2 API gateway input envelope."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(envelope, dict):
        return {
            "ok": False,
            "errors": ["envelope_must_be_object"],
            "warnings": [],
        }

    for field in REQUIRED_INPUT_FIELDS:
        if field not in envelope:
            errors.append(f"missing_required_field:{field}")

    operation = envelope.get("operation")
    if operation is not None and operation not in ALLOWED_OPERATIONS:
        errors.append(f"unsupported_operation:{operation}")

    for object_field in ["payload", "metadata", "oak_context"]:
        if object_field in envelope and not isinstance(envelope[object_field], dict):
            errors.append(f"field_must_be_object:{object_field}")

    metadata = envelope.get("metadata") if isinstance(envelope.get("metadata"), dict) else {}
    oak_context = envelope.get("oak_context") if isinstance(envelope.get("oak_context"), dict) else {}

    flagged = sorted(flag for flag in PRODUCTION_ONLY_FLAGS if metadata.get(flag) or oak_context.get(flag))
    if flagged:
        warnings.append("human_review_required:" + ",".join(flagged))

    if not envelope.get("request_id"):
        errors.append("request_id_empty")
    if not envelope.get("namespace"):
        warnings.append("namespace_empty_or_missing")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def oak_gate(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return the OAK pass/fail/review gate for an input envelope."""
    validation = validate_input_envelope(envelope)
    review_required = any(warning.startswith("human_review_required") for warning in validation["warnings"])
    if validation["errors"]:
        status = "FAIL"
    elif review_required:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"
    return {
        "status": status,
        "validation": validation,
        "review_required": review_required,
        "external_actions_allowed": False,
        "production_billing_allowed": False,
    }


def default_handler(envelope: dict[str, Any]) -> dict[str, Any]:
    """Deterministic placeholder handler for allowed operations."""
    return {
        "accepted": True,
        "operation": envelope.get("operation"),
        "message": "placeholder_handler_only",
        "payload_summary": sorted(envelope.get("payload", {}).keys()) if isinstance(envelope.get("payload"), dict) else [],
    }


def response_envelope(
    request_id: str | None,
    status: str,
    result: dict[str, Any] | None,
    warnings: list[str],
    errors: list[str],
    oak: dict[str, Any],
) -> dict[str, Any]:
    """Build the minimal AUTO2 API gateway output envelope."""
    return {
        "request_id": request_id,
        "status": status,
        "result": result or {},
        "warnings": warnings,
        "errors": errors,
        "oak_status": oak["status"],
        "residue_report": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "external_actions_allowed": False,
            "production_billing_allowed": False,
        },
        "next_action": "fix_input" if errors else ("human_review" if oak["review_required"] else "ready_for_next_p0_card"),
        "generated_at": now_iso(),
    }


def gateway_core(
    envelope: dict[str, Any],
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Route a validated envelope to a deterministic offline handler."""
    oak = oak_gate(envelope)
    validation = oak["validation"]
    if not validation["ok"]:
        return response_envelope(
            request_id=envelope.get("request_id") if isinstance(envelope, dict) else None,
            status="error",
            result=None,
            warnings=validation["warnings"],
            errors=validation["errors"],
            oak=oak,
        )

    operation = envelope["operation"]
    handler_map = handlers or {}
    handler = handler_map.get(operation, default_handler)
    result = handler(envelope)
    status = "review_required" if oak["review_required"] else "ok"
    return response_envelope(
        request_id=envelope.get("request_id"),
        status=status,
        result=result,
        warnings=validation["warnings"],
        errors=[],
        oak=oak,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", help="Path to a JSON request envelope fixture")
    args = parser.parse_args()
    fixture = pathlib.Path(args.fixture)
    envelope = json.loads(fixture.read_text(encoding="utf-8"))
    print(json.dumps(gateway_core(envelope), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
