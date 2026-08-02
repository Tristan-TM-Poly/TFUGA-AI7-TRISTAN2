"""Universal immutable action models for Ω-LEGAL-PRODUCTION-OS-T∞.

This module models requests and authority. It does not send email, move money,
sign documents, submit government filings, incorporate a company, publish a
release, or deploy production infrastructure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping


_ACTION_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,79}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORBIDDEN_KEY_PARTS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "private_key",
        "access_token",
        "refresh_token",
        "api_key",
        "credit_card",
        "card_number",
        "bank_account_number",
        "sin",
        "social_insurance",
    }
)


class ActionType(str, Enum):
    EXTERNAL_MAIL = "EXTERNAL_MAIL"
    RELEASE = "RELEASE"
    PAYMENT = "PAYMENT"
    SIGNATURE = "SIGNATURE"
    GOVERNMENT_FILING = "GOVERNMENT_FILING"
    INCORPORATION = "INCORPORATION"
    PRODUCTION_ACTIVATION = "PRODUCTION_ACTIVATION"


class ActionState(str, Enum):
    DRAFT = "DRAFT"
    NORMALIZED = "NORMALIZED"
    VALIDATED = "VALIDATED"
    RISK_SCORED = "RISK_SCORED"
    AUTHORITY_RESOLVED = "AUTHORITY_RESOLVED"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    RESERVED = "RESERVED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    EFFECT_CONFIRMED = "EFFECT_CONFIRMED"
    RECONCILED = "RECONCILED"
    CLOSED = "CLOSED"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    REQUIRE_SECOND_APPROVAL = "REQUIRE_SECOND_APPROVAL"
    REQUIRE_PROFESSIONAL_REVIEW = "REQUIRE_PROFESSIONAL_REVIEW"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    EFFECT_UNKNOWN = "EFFECT_UNKNOWN"
    RECONCILIATION_FAILED = "RECONCILIATION_FAILED"
    QUARANTINED = "QUARANTINED"
    BLOCKED = "BLOCKED"
    ROLLED_BACK = "ROLLED_BACK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GateDecision(str, Enum):
    ALLOW_DRY_RUN = "ALLOW_DRY_RUN"
    ALLOW_EXECUTION = "ALLOW_EXECUTION"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_TWO_APPROVALS = "REQUIRE_TWO_APPROVALS"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    BLOCK = "BLOCK"


_ALLOWED_TRANSITIONS: dict[ActionState, frozenset[ActionState]] = {
    ActionState.DRAFT: frozenset({ActionState.NORMALIZED, ActionState.BLOCKED, ActionState.QUARANTINED}),
    ActionState.NORMALIZED: frozenset({ActionState.VALIDATED, ActionState.REQUIRE_INFORMATION, ActionState.BLOCKED}),
    ActionState.VALIDATED: frozenset({ActionState.RISK_SCORED, ActionState.BLOCKED}),
    ActionState.RISK_SCORED: frozenset({ActionState.AUTHORITY_RESOLVED, ActionState.REQUIRE_PROFESSIONAL_REVIEW, ActionState.BLOCKED}),
    ActionState.AUTHORITY_RESOLVED: frozenset({ActionState.READY_FOR_APPROVAL, ActionState.REQUIRE_INFORMATION, ActionState.BLOCKED}),
    ActionState.READY_FOR_APPROVAL: frozenset({ActionState.APPROVED, ActionState.REQUIRE_SECOND_APPROVAL, ActionState.REVOKED, ActionState.EXPIRED}),
    ActionState.REQUIRE_SECOND_APPROVAL: frozenset({ActionState.APPROVED, ActionState.REVOKED, ActionState.EXPIRED}),
    ActionState.REQUIRE_PROFESSIONAL_REVIEW: frozenset({ActionState.READY_FOR_APPROVAL, ActionState.BLOCKED, ActionState.REVOKED}),
    ActionState.APPROVED: frozenset({ActionState.RESERVED, ActionState.REVOKED, ActionState.EXPIRED}),
    ActionState.RESERVED: frozenset({ActionState.EXECUTION_STARTED, ActionState.ROLLED_BACK, ActionState.EXPIRED}),
    ActionState.EXECUTION_STARTED: frozenset({ActionState.PROVIDER_ACCEPTED, ActionState.PROVIDER_REJECTED, ActionState.EFFECT_UNKNOWN}),
    ActionState.PROVIDER_ACCEPTED: frozenset({ActionState.EFFECT_CONFIRMED, ActionState.EFFECT_UNKNOWN, ActionState.RECONCILIATION_FAILED}),
    ActionState.EFFECT_CONFIRMED: frozenset({ActionState.RECONCILED, ActionState.RECONCILIATION_FAILED}),
    ActionState.RECONCILED: frozenset({ActionState.CLOSED}),
    ActionState.RECONCILIATION_FAILED: frozenset({ActionState.RECONCILED, ActionState.EFFECT_UNKNOWN, ActionState.BLOCKED}),
    ActionState.EFFECT_UNKNOWN: frozenset({ActionState.EFFECT_CONFIRMED, ActionState.RECONCILIATION_FAILED, ActionState.BLOCKED}),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    instant = value or utc_now()
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [canonicalize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        canonicalize(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def detect_forbidden_payload_keys(value: Any, path: str = "payload") -> tuple[str, ...]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().casefold()
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                findings.append(f"{path}.{key}")
            findings.extend(detect_forbidden_payload_keys(item, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(detect_forbidden_payload_keys(item, f"{path}[{index}]"))
    return tuple(sorted(set(findings)))


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    action_hash: str
    approver: str
    role: str
    approved_at: str
    scope: str = "ONE_ACTION"
    note: str = ""

    @classmethod
    def create(
        cls,
        action: "ExternalActionEnvelope",
        *,
        approver: str,
        role: str,
        note: str = "",
        approved_at: datetime | None = None,
    ) -> "ApprovalRecord":
        return cls(
            action_hash=action.action_hash,
            approver=approver.strip(),
            role=role.strip(),
            approved_at=iso_utc(approved_at),
            note=note,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApprovalRecord":
        return cls(
            action_hash=str(data["action_hash"]),
            approver=str(data["approver"]),
            role=str(data["role"]),
            approved_at=str(data["approved_at"]),
            scope=str(data.get("scope", "ONE_ACTION")),
            note=str(data.get("note", "")),
        )

    def validate_for(self, action: "ExternalActionEnvelope") -> tuple[str, ...]:
        reasons: list[str] = []
        if self.scope != "ONE_ACTION":
            reasons.append("approval_scope_invalid")
        if self.action_hash != action.action_hash:
            reasons.append("approval_hash_mismatch")
        if not self.approver.strip():
            reasons.append("approval_approver_missing")
        if not self.role.strip():
            reasons.append("approval_role_missing")
        try:
            datetime.fromisoformat(self.approved_at.replace("Z", "+00:00"))
        except ValueError:
            reasons.append("approval_timestamp_invalid")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    grant_id: str
    person_id: str
    company_id: str
    role: str
    permissions: tuple[str, ...]
    amount_limit_cad: float | None = None
    jurisdictions: tuple[str, ...] = ()
    valid_from: str | None = None
    valid_until: str | None = None
    revoked: bool = False
    evidence_hash: str | None = None

    def permits(
        self,
        permission: str,
        *,
        company_id: str,
        amount_cad: float | None = None,
        jurisdiction: str | None = None,
        at: datetime | None = None,
    ) -> bool:
        if self.revoked or company_id != self.company_id or permission not in self.permissions:
            return False
        instant = at or utc_now()
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        if self.valid_from and instant < datetime.fromisoformat(self.valid_from.replace("Z", "+00:00")):
            return False
        if self.valid_until and instant > datetime.fromisoformat(self.valid_until.replace("Z", "+00:00")):
            return False
        if amount_cad is not None and self.amount_limit_cad is not None and amount_cad > self.amount_limit_cad:
            return False
        if jurisdiction and self.jurisdictions and jurisdiction not in self.jurisdictions:
            return False
        return True


@dataclass(frozen=True, slots=True)
class ExternalActionEnvelope:
    action_id: str
    action_type: ActionType
    company_id: str
    requested_by: str
    requested_at: str
    purpose: str
    payload: Mapping[str, Any]
    required_approvals: int = 1
    professional_review_required: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    state: ActionState = ActionState.DRAFT
    approvals: tuple[ApprovalRecord, ...] = ()
    source_issue: int | None = None
    source_commit: str | None = None
    policy_id: str = "DEFAULT-DENY"
    evidence_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _ACTION_ID.fullmatch(self.action_id):
            raise ValueError("action_id must be a stable uppercase identifier")
        if not self.company_id.strip() or not self.requested_by.strip() or not self.purpose.strip():
            raise ValueError("company_id, requested_by and purpose are required")
        if self.required_approvals not in {1, 2}:
            raise ValueError("required_approvals must be 1 or 2")
        forbidden = detect_forbidden_payload_keys(self.payload)
        if forbidden:
            raise ValueError("secret-like payload keys are forbidden: " + ",".join(forbidden))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExternalActionEnvelope":
        return cls(
            action_id=str(data["action_id"]),
            action_type=ActionType(str(data["action_type"])),
            company_id=str(data["company_id"]),
            requested_by=str(data["requested_by"]),
            requested_at=str(data["requested_at"]),
            purpose=str(data["purpose"]),
            payload=dict(data.get("payload", {})),
            required_approvals=int(data.get("required_approvals", 1)),
            professional_review_required=bool(data.get("professional_review_required", False)),
            risk_level=RiskLevel(str(data.get("risk_level", RiskLevel.MEDIUM.value))),
            state=ActionState(str(data.get("state", ActionState.DRAFT.value))),
            approvals=tuple(ApprovalRecord.from_mapping(item) for item in data.get("approvals", ())),
            source_issue=int(data["source_issue"]) if data.get("source_issue") is not None else None,
            source_commit=str(data["source_commit"]) if data.get("source_commit") else None,
            policy_id=str(data.get("policy_id", "DEFAULT-DENY")),
            evidence_ids=tuple(str(item) for item in data.get("evidence_ids", ())),
            metadata=dict(data.get("metadata", {})),
        )

    def request_payload(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "company_id": self.company_id,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
            "purpose": self.purpose,
            "payload": canonicalize(self.payload),
            "required_approvals": self.required_approvals,
            "professional_review_required": self.professional_review_required,
            "risk_level": self.risk_level.value,
            "source_issue": self.source_issue,
            "source_commit": self.source_commit,
            "policy_id": self.policy_id,
            "evidence_ids": list(self.evidence_ids),
            "metadata": canonicalize(self.metadata),
        }

    @property
    def action_hash(self) -> str:
        return hash_payload(self.request_payload())

    def to_mapping(self) -> dict[str, Any]:
        result = self.request_payload()
        result.update(
            {
                "state": self.state.value,
                "approvals": [asdict(item) for item in self.approvals],
                "action_hash": self.action_hash,
            }
        )
        return result

    def add_approval(self, approval: ApprovalRecord) -> "ExternalActionEnvelope":
        reasons = approval.validate_for(self)
        if reasons:
            raise ValueError("invalid approval: " + ",".join(reasons))
        if any(item.approver.casefold() == approval.approver.casefold() for item in self.approvals):
            raise ValueError("duplicate approver")
        return replace(self, approvals=self.approvals + (approval,))

    def transition(self, target: ActionState) -> "ExternalActionEnvelope":
        if target == self.state:
            return self
        allowed = _ALLOWED_TRANSITIONS.get(self.state, frozenset())
        if target not in allowed:
            raise ValueError(f"invalid action transition: {self.state.value}->{target.value}")
        return replace(self, state=target)

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        try:
            datetime.fromisoformat(self.requested_at.replace("Z", "+00:00"))
        except ValueError:
            reasons.append("requested_at_invalid")
        if self.source_commit and not re.fullmatch(r"[0-9a-f]{7,40}", self.source_commit):
            reasons.append("source_commit_invalid")
        for evidence_id in self.evidence_ids:
            if evidence_id.startswith("sha256:") and not _SHA256.fullmatch(evidence_id):
                reasons.append("evidence_hash_invalid")
        return tuple(sorted(set(reasons)))
