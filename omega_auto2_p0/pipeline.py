"""Omega AUTO2 P0 integration pipeline.

Synthetic request -> API gateway -> spectral core -> usage event -> combined OAK.

This pipeline is offline-only. It does not call external systems, does not use
customer data, and does not enable production behavior.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scripts.omega_auto2_api_gateway_p0 import gateway_core
from scripts.omega_auto2_spectral_core_p0 import oak_report as spectral_oak_report
from scripts.omega_auto2_usage_events_p0 import normalize_usage_event

from .oak import OAK_FAIL, OAK_PASS, combine_oak_status, envelope_from_module_report


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_usage_event(request: dict[str, Any], gateway: dict[str, Any], spectral: dict[str, Any]) -> dict[str, Any]:
    """Create a synthetic usage event from a completed P0 request."""
    return {
        "event_id": f"evt_{request.get('request_id', 'unknown')}",
        "request_id": request.get("request_id", "unknown"),
        "namespace": request.get("namespace", "synthetic"),
        "operation": request.get("operation", "test_run"),
        "unit_type": "spectrum" if request.get("operation") == "validate_spectrum" else "request",
        "units": 1,
        "timestamp": _now_iso(),
        "oak_context": {
            "mode": "offline_integration_test",
            "gateway_status": gateway.get("oak_status"),
            "spectral_status": spectral.get("status"),
            "production_use": False,
            "contains_customer_data": False,
        },
    }


def run_p0_pipeline(request: dict[str, Any]) -> dict[str, Any]:
    """Run the integrated P0 stack and return a combined OAK report."""
    gateway = gateway_core(request)
    gateway_env = envelope_from_module_report(gateway)

    spectral: dict[str, Any] = {}
    usage: dict[str, Any] = {}
    module_statuses = [gateway_env.oak_status]

    if gateway_env.oak_status == OAK_FAIL:
        combined_status = OAK_FAIL
        next_action = "fix_gateway_input"
    else:
        payload = request.get("payload", {})
        spectral = spectral_oak_report(payload)
        spectral_env = envelope_from_module_report(
            {
                "oak_status": spectral.get("status"),
                "errors": spectral.get("schema", {}).get("errors", []),
                "warnings": spectral.get("schema", {}).get("warnings", []),
                "residue_report": spectral.get("residue_report", {}),
                "external_actions_allowed": spectral.get("external_actions_allowed", False),
                "production_use_allowed": spectral.get("production_use_allowed", False),
                "next_action": spectral.get("next_action"),
            }
        )
        module_statuses.append(spectral_env.oak_status)

        usage_event = make_usage_event(request, gateway, spectral)
        usage = normalize_usage_event(usage_event)
        usage_env = envelope_from_module_report(usage)
        module_statuses.append(usage_env.oak_status)

        combined_status = combine_oak_status(module_statuses)
        next_action = "ready_for_spectral_cleaning_p0" if combined_status == OAK_PASS else "fix_p0_residues"

    return {
        "oak_status": combined_status,
        "module_statuses": {
            "gateway": gateway.get("oak_status"),
            "spectral_core": spectral.get("status"),
            "usage_events": usage.get("oak_status"),
        },
        "gateway": gateway,
        "spectral_core": spectral,
        "usage_events": usage,
        "residue_report": {
            "module_count": len([value for value in [gateway, spectral, usage] if value]),
            "failed_modules": [name for name, status in {
                "gateway": gateway.get("oak_status"),
                "spectral_core": spectral.get("status"),
                "usage_events": usage.get("oak_status"),
            }.items() if status == OAK_FAIL],
            "external_actions_allowed": False,
            "production_use_allowed": False,
        },
        "external_actions_allowed": False,
        "production_use_allowed": False,
        "next_action": next_action,
        "generated_at": _now_iso(),
    }
