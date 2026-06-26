from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SENSITIVE_ACTIONS = {
    "delete_files",
    "public_publish",
    "external_email",
    "spend_money",
    "change_permissions",
    "legal_commitment",
    "medical_decision",
    "ip_disclosure",
}


@dataclass(frozen=True)
class FrictionTensor:
    """Tenseur minimal de friction pour décider quoi automatiser.

    Toutes les dimensions sont normalisées entre 0 et 1.
    """

    time_cost: float
    repetition: float
    cognitive_load: float
    error_risk: float
    value_loss: float
    urgency: float
    complexity: float
    human_dependency: float
    build_cost: float = 0.3
    safety_risk: float = 0.3

    def clamp(self) -> "FrictionTensor":
        values = {
            key: max(0.0, min(1.0, float(value)))
            for key, value in self.__dict__.items()
        }
        return FrictionTensor(**values)


@dataclass
class Workflow:
    id: str
    name: str
    purpose: str
    trigger: dict[str, Any]
    inputs: list[str]
    steps: list[str]
    outputs: list[str]
    permissions: dict[str, list[str]]
    oak: dict[str, Any]
    rollback: dict[str, Any] = field(default_factory=lambda: {"possible": True, "method": "remove generated artifacts"})
    telemetry: dict[str, Any] = field(default_factory=lambda: {"track": ["time_saved", "errors", "usefulness"]})
    status: str = "draft"
    version: str = "0.1.0"
    owner: str = "Tristan"

    def forbidden_actions(self) -> set[str]:
        return set(self.permissions.get("forbidden", []))

    def write_permissions(self) -> set[str]:
        return set(self.permissions.get("write", []))

    def sensitive_writes(self) -> set[str]:
        return self.write_permissions().intersection(SENSITIVE_ACTIONS)

    def to_dict(self) -> dict[str, Any]:
        return {"workflow": self.__dict__}


@dataclass(frozen=True)
class OAKReport:
    clarity: float
    safety: float
    reversibility: float
    usefulness: float
    cost_control: float
    legal_ip: float
    final_score: float
    status: str
    blockers: list[str]
    warnings: list[str]
    human_approval_required_for: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"oak_report": self.__dict__}
