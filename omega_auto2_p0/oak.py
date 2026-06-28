"""Shared OAK envelope primitives for Omega AUTO2 P0.

The envelope standard keeps modules composable while preserving hard locks:
external actions and production use are disabled by default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OAK_PASS = "PASS"
OAK_FAIL = "FAIL"
OAK_REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class OAKEnvelope:
    oak_status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    residue_report: dict[str, Any] = field(default_factory=dict)
    external_actions_allowed: bool = False
    production_use_allowed: bool = False
    next_action: str = "ready_for_next_p0_card"

    def to_dict(self) -> dict[str, Any]:
        return {
            "oak_status": self.oak_status,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "residue_report": dict(self.residue_report),
            "external_actions_allowed": self.external_actions_allowed,
            "production_use_allowed": self.production_use_allowed,
            "next_action": self.next_action,
        }


def combine_oak_status(statuses: list[str]) -> str:
    """Combine module statuses into a conservative global OAK status."""
    if any(status == OAK_FAIL for status in statuses):
        return OAK_FAIL
    if any(status == OAK_REVIEW_REQUIRED for status in statuses):
        return OAK_REVIEW_REQUIRED
    return OAK_PASS


def envelope_from_module_report(report: dict[str, Any], default_next_action: str = "ready_for_next_p0_card") -> OAKEnvelope:
    """Normalize existing P0 module reports into the shared envelope."""
    status = report.get("oak_status") or report.get("status") or OAK_FAIL
    if status == "ok":
        status = OAK_PASS
    if status == "error":
        status = OAK_FAIL

    errors = list(report.get("errors", []))
    warnings = list(report.get("warnings", []))
    residue = dict(report.get("residue_report", {}))
    if "error_count" not in residue:
        residue["error_count"] = len(errors)
    if "warning_count" not in residue:
        residue["warning_count"] = len(warnings)

    return OAKEnvelope(
        oak_status=status,
        errors=errors,
        warnings=warnings,
        residue_report=residue,
        external_actions_allowed=bool(report.get("external_actions_allowed", False)),
        production_use_allowed=bool(report.get("production_use_allowed", False)),
        next_action=report.get("next_action", default_next_action),
    )
