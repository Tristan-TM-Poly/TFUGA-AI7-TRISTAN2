"""Small validators for ActionDNA payloads."""

from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = ("name", "system", "action_type")
RISK_AXES = ("legal", "ip", "finance", "safety", "privacy", "reputation", "irreversibility")


def validate_payload(data: dict[str, Any]) -> list[str]:
    """Return validation errors for a raw manifest payload.

    The validator is dependency-free and intentionally conservative. It does not
    execute any action.
    """

    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if not str(data.get(field, "")).strip():
            errors.append(f"missing_required_field:{field}")

    risk = data.get("risk", {}) or {}
    if not isinstance(risk, dict):
        errors.append("risk_must_be_object")
        return errors

    for axis, value in risk.items():
        if axis not in RISK_AXES:
            errors.append(f"unknown_risk_axis:{axis}")
            continue
        if not isinstance(value, int) or not 0 <= value <= 5:
            errors.append(f"risk_axis_out_of_range:{axis}")

    if data.get("destructive") and not data.get("rollback"):
        errors.append("destructive_requires_rollback")

    action_type = str(data.get("action_type", "")).lower()
    system = str(data.get("system", "")).lower()
    metadata = data.get("metadata", {}) or {}
    calendar_like = system == "calendar" or "calendar" in action_type or "schedule" in action_type
    if calendar_like and not metadata.get("timezone"):
        errors.append("calendar_like_action_requires_timezone")

    return errors
