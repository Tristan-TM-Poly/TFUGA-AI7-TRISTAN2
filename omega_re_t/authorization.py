"""Fail-closed authorization contracts for Ω-RE-T∞.

The module is deliberately generic: it models whether an experiment is allowed,
not how to perform intrusive actions. Every campaign must declare ownership or
permission, bounded actions, data classes, retention, and stop conditions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from json import dumps, loads
from typing import Any, Iterable, Mapping


class AuthorizationAction(str, Enum):
    OBSERVE = "observe"
    QUERY = "query"
    RESET = "reset"
    PERTURB_REVERSIBLE = "perturb_reversible"
    SIMULATE = "simulate"
    STORE = "store"
    EXPORT_REPORT = "export_report"
    IMPLEMENT_CLEAN_ROOM = "implement_clean_room"
    DESTRUCTIVE_TEST = "destructive_test"
    EXTERNAL_COMMUNICATION = "external_communication"


class DataClass(str, Enum):
    SYNTHETIC = "synthetic"
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PERSONAL = "personal"
    REGULATED = "regulated"


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_REVIEW = "require_review"


@dataclass(frozen=True, slots=True)
class StopCondition:
    code: str
    description: str
    severity: int = 5

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.description.strip():
            raise ValueError("stop condition code and description are required")
        if not 1 <= self.severity <= 10:
            raise ValueError("severity must be in [1, 10]")


@dataclass(frozen=True, slots=True)
class AuthorizationContract:
    contract_id: str
    subject_id: str
    authority: str
    purpose: str
    allowed_actions: frozenset[AuthorizationAction]
    denied_actions: frozenset[AuthorizationAction] = frozenset()
    allowed_data_classes: frozenset[DataClass] = frozenset({DataClass.SYNTHETIC})
    valid_from: str | None = None
    valid_until: str | None = None
    max_experiments: int | None = None
    max_cost: float | None = None
    retention_days: int = 30
    external_release_allowed: bool = False
    clean_room_required: bool = False
    stop_conditions: tuple[StopCondition, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, label in (
            (self.contract_id, "contract_id"),
            (self.subject_id, "subject_id"),
            (self.authority, "authority"),
            (self.purpose, "purpose"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
        overlap = self.allowed_actions & self.denied_actions
        if overlap:
            raise ValueError(
                "actions cannot be both allowed and denied: "
                f"{sorted(x.value for x in overlap)}"
            )
        if self.max_experiments is not None and self.max_experiments <= 0:
            raise ValueError("max_experiments must be positive")
        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost cannot be negative")
        if self.retention_days < 0:
            raise ValueError("retention_days cannot be negative")
        self._parse_time(self.valid_from)
        self._parse_time(self.valid_until)
        if self.valid_from and self.valid_until:
            if self._parse_time(self.valid_from) >= self._parse_time(self.valid_until):
                raise ValueError("valid_from must precede valid_until")

    @staticmethod
    def _parse_time(value: str | None) -> datetime | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def is_active(self, at: datetime | None = None) -> bool:
        instant = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        start = self._parse_time(self.valid_from)
        end = self._parse_time(self.valid_until)
        return (start is None or instant >= start) and (end is None or instant <= end)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "subject_id": self.subject_id,
            "authority": self.authority,
            "purpose": self.purpose,
            "allowed_actions": sorted(x.value for x in self.allowed_actions),
            "denied_actions": sorted(x.value for x in self.denied_actions),
            "allowed_data_classes": sorted(x.value for x in self.allowed_data_classes),
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "max_experiments": self.max_experiments,
            "max_cost": self.max_cost,
            "retention_days": self.retention_days,
            "external_release_allowed": self.external_release_allowed,
            "clean_room_required": self.clean_room_required,
            "stop_conditions": [asdict(x) for x in self.stop_conditions],
            "metadata": dict(self.metadata),
        }

    @property
    def digest(self) -> str:
        payload = dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_json(self, *, indent: int | None = 2) -> str:
        return dumps(
            self.canonical_dict(),
            sort_keys=True,
            indent=indent,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, text: str) -> "AuthorizationContract":
        data = loads(text)
        return cls(
            contract_id=data["contract_id"],
            subject_id=data["subject_id"],
            authority=data["authority"],
            purpose=data["purpose"],
            allowed_actions=frozenset(
                AuthorizationAction(x) for x in data["allowed_actions"]
            ),
            denied_actions=frozenset(
                AuthorizationAction(x) for x in data.get("denied_actions", [])
            ),
            allowed_data_classes=frozenset(
                DataClass(x)
                for x in data.get("allowed_data_classes", ["synthetic"])
            ),
            valid_from=data.get("valid_from"),
            valid_until=data.get("valid_until"),
            max_experiments=data.get("max_experiments"),
            max_cost=data.get("max_cost"),
            retention_days=int(data.get("retention_days", 30)),
            external_release_allowed=bool(
                data.get("external_release_allowed", False)
            ),
            clean_room_required=bool(data.get("clean_room_required", False)),
            stop_conditions=tuple(
                StopCondition(**x) for x in data.get("stop_conditions", [])
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    action: AuthorizationAction
    data_class: DataClass
    experiment_index: int = 0
    accumulated_cost: float = 0.0
    external_release: bool = False
    clean_room: bool = False
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    decision: Decision
    reasons: tuple[str, ...]
    contract_digest: str

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


class AuthorizationGate:
    """Evaluate requests with explicit fail-closed rules."""

    def __init__(self, contract: AuthorizationContract):
        self.contract = contract

    def evaluate(
        self,
        request: AuthorizationRequest,
        *,
        at: datetime | None = None,
    ) -> AuthorizationDecision:
        reasons: list[str] = []
        hard_denial = False
        review = False
        if not self.contract.is_active(at):
            hard_denial = True
            reasons.append("contract_inactive")
        if request.action in self.contract.denied_actions:
            hard_denial = True
            reasons.append("action_explicitly_denied")
        if request.action not in self.contract.allowed_actions:
            hard_denial = True
            reasons.append("action_not_allowed")
        if request.data_class not in self.contract.allowed_data_classes:
            hard_denial = True
            reasons.append("data_class_not_allowed")
        if (
            self.contract.max_experiments is not None
            and request.experiment_index >= self.contract.max_experiments
        ):
            hard_denial = True
            reasons.append("experiment_budget_exhausted")
        if (
            self.contract.max_cost is not None
            and request.accumulated_cost > self.contract.max_cost
        ):
            hard_denial = True
            reasons.append("cost_budget_exceeded")
        if request.external_release and not self.contract.external_release_allowed:
            hard_denial = True
            reasons.append("external_release_not_allowed")
        if self.contract.clean_room_required and not request.clean_room:
            review = True
            reasons.append("clean_room_required")
        if request.action in {
            AuthorizationAction.DESTRUCTIVE_TEST,
            AuthorizationAction.EXTERNAL_COMMUNICATION,
        }:
            review = True
            reasons.append("sensitive_action_requires_review")
        if hard_denial:
            decision = Decision.DENY
        elif review:
            decision = Decision.REQUIRE_REVIEW
        else:
            decision = Decision.ALLOW
            reasons.append("within_declared_scope")
        return AuthorizationDecision(
            decision,
            tuple(reasons),
            self.contract.digest,
        )

    def require(
        self,
        request: AuthorizationRequest,
        *,
        at: datetime | None = None,
    ) -> None:
        result = self.evaluate(request, at=at)
        if not result.allowed:
            raise PermissionError(
                f"authorization {result.decision.value}: "
                f"{', '.join(result.reasons)}"
            )


def synthetic_contract(
    subject_id: str = "synthetic-system",
) -> AuthorizationContract:
    return AuthorizationContract(
        contract_id=f"contract-{subject_id}",
        subject_id=subject_id,
        authority="local synthetic benchmark",
        purpose="OAK-safe mechanism reconstruction",
        allowed_actions=frozenset(
            {
                AuthorizationAction.OBSERVE,
                AuthorizationAction.QUERY,
                AuthorizationAction.RESET,
                AuthorizationAction.PERTURB_REVERSIBLE,
                AuthorizationAction.SIMULATE,
                AuthorizationAction.STORE,
                AuthorizationAction.EXPORT_REPORT,
            }
        ),
        denied_actions=frozenset(
            {
                AuthorizationAction.DESTRUCTIVE_TEST,
                AuthorizationAction.EXTERNAL_COMMUNICATION,
            }
        ),
        allowed_data_classes=frozenset({DataClass.SYNTHETIC}),
        max_experiments=10_000,
        max_cost=10_000.0,
        retention_days=365,
        external_release_allowed=True,
        stop_conditions=(
            StopCondition(
                "unexpected_scope",
                "Stop when the observed subject differs from the declared synthetic target",
                10,
            ),
        ),
    )


def authorize_batch(
    gate: AuthorizationGate,
    requests: Iterable[AuthorizationRequest],
) -> tuple[AuthorizationDecision, ...]:
    return tuple(gate.evaluate(request) for request in requests)
