"""Core data structures for Ω-ACTION-EXT-T.

This module intentionally has no external dependencies. It is safe to import in
small scripts, notebooks, CI checks, and future connector adapters.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Decision(str, Enum):
    """OAKGate decision classes."""

    ALLOW_AUTO = "allow_auto"
    ALLOW_DRAFT = "allow_draft"
    NEEDS_APPROVAL = "needs_approval"
    REQUIRE_EXPERT = "require_expert"
    BLOCK = "block"


class AutonomyLevel(str, Enum):
    """External action autonomy ladder."""

    L0_NO_ACTION = "L0_no_action"
    L1_DRAFT_ONLY = "L1_draft_only"
    L2_REVERSIBLE_SAFE = "L2_reversible_safe"
    L3_APPROVED_EXECUTION = "L3_approved_execution"
    L4_CO_SIGNED = "L4_co_signed"
    L5_BLOCKED = "L5_blocked"


@dataclass(frozen=True)
class RiskTensor:
    """Multi-axis risk score for external actions.

    Axes are intentionally simple integers from 0 to 5:
    0 = none/negligible, 5 = critical.
    """

    legal: int = 0
    ip: int = 0
    finance: int = 0
    safety: int = 0
    privacy: int = 0
    reputation: int = 0
    irreversibility: int = 0

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not 0 <= value <= 5:
                raise ValueError(f"risk axis {key!r} must be in [0, 5], got {value}")

    @property
    def total(self) -> int:
        return sum(asdict(self).values())

    @property
    def max_axis(self) -> int:
        return max(asdict(self).values())

    def to_dict(self) -> dict[str, int]:
        data = asdict(self)
        data["total"] = self.total
        data["max_axis"] = self.max_axis
        return data


@dataclass(frozen=True)
class ActionDNA:
    """Serializable description of a proposed external action."""

    name: str
    system: str
    action_type: str
    risk: RiskTensor = field(default_factory=RiskTensor)
    intent: str = ""
    target: str | None = None
    reversible: bool = False
    rollback: str | None = None
    approved: bool = False
    public: bool = False
    destructive: bool = False
    touches_humans: bool = False
    touches_money: bool = False
    touches_ip: bool = False
    touches_health: bool = False
    touches_safety: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_sovereign_attention(self) -> bool:
        return any(
            [
                self.public,
                self.destructive,
                self.touches_humans,
                self.touches_money,
                self.touches_ip,
                self.touches_health,
                self.touches_safety,
                self.risk.max_axis >= 3,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.to_dict()
        data["requires_sovereign_attention"] = self.requires_sovereign_attention
        return data


@dataclass(frozen=True)
class DryRunReport:
    """Non-executing report produced before any external action."""

    action: ActionDNA
    decision: Decision
    autonomy_level: AutonomyLevel
    reasons: list[str]
    required_approvals: list[str] = field(default_factory=list)
    expected_effects: list[str] = field(default_factory=list)
    rollback_plan: str | None = None
    blocked_by: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "decision": self.decision.value,
            "autonomy_level": self.autonomy_level.value,
            "reasons": list(self.reasons),
            "required_approvals": list(self.required_approvals),
            "expected_effects": list(self.expected_effects),
            "rollback_plan": self.rollback_plan,
            "blocked_by": list(self.blocked_by),
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class ProofOfExecution:
    """Proof record for an action that was executed by a future connector."""

    action_id: str
    system: str
    artifact_type: str
    artifact_id: str
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "omega_action_ext_t"
    input_hash: str | None = None
    output_hash: str | None = None
    observation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
