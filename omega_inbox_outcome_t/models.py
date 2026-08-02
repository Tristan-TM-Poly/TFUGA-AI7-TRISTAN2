"""Typed records for Ω-INBOX-TO-OUTCOME-T.

The package models intake, case planning, deliverable generation, validation,
routing, and bounded reply decisions. It does not grant itself legal authority,
consent, identity, contract scope, or permission to transmit confidential data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Channel(str, Enum):
    EMAIL = "email"
    GITHUB = "github"
    DRIVE = "drive"
    DROPBOX = "dropbox"
    PORTAL = "portal"
    API = "api"
    SFTP = "sftp"
    SIGNATURE = "signature"
    GOVERNMENT_PORTAL = "government_portal"


class IntakeStatus(str, Enum):
    RECEIVED = "RECEIVED"
    QUARANTINED = "QUARANTINED"
    TRIAGED = "TRIAGED"
    CASE_OPENED = "CASE_OPENED"
    PLANNED = "PLANNED"
    PRODUCING = "PRODUCING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    READY_TO_DISPATCH = "READY_TO_DISPATCH"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class Intent(str, Enum):
    ACKNOWLEDGMENT = "ACKNOWLEDGMENT"
    STATUS_REQUEST = "STATUS_REQUEST"
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    TECHNICAL_REPORT = "TECHNICAL_REPORT"
    BUG_REPORT = "BUG_REPORT"
    SUPPORT_QUESTION = "SUPPORT_QUESTION"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    PROPOSAL_REQUEST = "PROPOSAL_REQUEST"
    QUOTE_REQUEST = "QUOTE_REQUEST"
    INVOICE_REQUEST = "INVOICE_REQUEST"
    PAYMENT_CHANGE = "PAYMENT_CHANGE"
    CONTRACT_OR_LEGAL = "CONTRACT_OR_LEGAL"
    IP_OR_CONFIDENTIAL = "IP_OR_CONFIDENTIAL"
    PRIVACY_REQUEST = "PRIVACY_REQUEST"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    GOVERNMENT_OR_TAX = "GOVERNMENT_OR_TAX"
    UNKNOWN = "UNKNOWN"


class RiskBand(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReplyDecision(str, Enum):
    AUTO_REPLY = "AUTO_REPLY"
    AUTO_PRODUCE_DRAFT_DISPATCH = "AUTO_PRODUCE_DRAFT_DISPATCH"
    AUTO_BOUNDED_DISPATCH = "AUTO_BOUNDED_DISPATCH"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_TWO_APPROVALS = "REQUIRE_TWO_APPROVALS"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REGENERATE = "REGENERATE"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CLIENT_CONFIDENTIAL = "client_confidential"
    PERSONAL = "personal"
    RESTRICTED = "restricted"
    SECRET = "secret"


@dataclass(slots=True)
class IntakeEvent:
    event_id: str
    channel: Channel
    provider: str
    account: str
    external_id: str
    sender_address: str
    sender_name: str
    subject: str
    body: str
    recipients: list[str]
    attachments: list[dict[str, Any]] = field(default_factory=list)
    language: str = "fr-CA"
    received_at: str = field(default_factory=utc_now)
    status: IntakeStatus = IntakeStatus.RECEIVED
    raw_hash: str | None = None
    externally_controlled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["channel"] = self.channel.value
        payload["status"] = self.status.value
        return payload


@dataclass(slots=True)
class ResolvedIdentity:
    person_id: str | None = None
    organization_id: str | None = None
    verified_addresses: list[str] = field(default_factory=list)
    relationship: str = "unknown"
    contract_id: str | None = None
    allowed_project_ids: list[str] = field(default_factory=list)
    allowed_data_classes: list[DataClass] = field(default_factory=lambda: [DataClass.PUBLIC])
    identity_confidence: float = 0.0
    organization_confidence: float = 0.0
    authority_confidence: float = 0.0
    may_receive_financial_documents: bool = False
    may_receive_source_code: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_data_classes"] = [item.value for item in self.allowed_data_classes]
        return payload


@dataclass(slots=True)
class RequestAnalysis:
    primary_intent: Intent
    secondary_intents: list[Intent] = field(default_factory=list)
    explicit_requests: list[str] = field(default_factory=list)
    implicit_requirements: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    requested_formats: list[str] = field(default_factory=list)
    deadline_text: str | None = None
    commercial: bool = False
    requested_data_class: DataClass = DataClass.PUBLIC
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["primary_intent"] = self.primary_intent.value
        payload["secondary_intents"] = [item.value for item in self.secondary_intents]
        payload["requested_data_class"] = self.requested_data_class.value
        return payload


@dataclass(slots=True)
class CaseRecord:
    case_id: str
    event_id: str
    company_id: str
    division_id: str
    identity: ResolvedIdentity
    analysis: RequestAnalysis
    status: IntakeStatus = IntakeStatus.CASE_OPENED
    thread_ids: list[str] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)
    deliverable_ids: list[str] = field(default_factory=list)
    approval_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["identity"] = self.identity.to_dict()
        payload["analysis"] = self.analysis.to_dict()
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class TaskSpec:
    task_id: str
    case_id: str
    action: str
    dependencies: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    reversible: bool = True
    external_effect: bool = False


@dataclass(slots=True)
class OutcomePlan:
    plan_id: str
    case_id: str
    objective: str
    tasks: list[TaskSpec]
    required_approvals: int = 0
    professional_review: bool = False
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeliverableManifest:
    deliverable_id: str
    case_id: str
    deliverable_type: str
    version: str
    company_id: str
    division_id: str
    input_refs: list[dict[str, Any]]
    outputs: list[dict[str, Any]]
    data_class: DataClass = DataClass.PUBLIC
    claims: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    approved_hash: str | None = None
    status: str = "DRAFT"
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["data_class"] = self.data_class.value
        return payload


@dataclass(frozen=True, slots=True)
class ValidationResult:
    deliverable_id: str
    status: ValidationStatus
    checks: dict[str, bool]
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(slots=True)
class AutonomousDeliveryContract:
    contract_id: str
    company_id: str
    division_id: str
    allowed_intents: list[Intent]
    allowed_response_types: list[str]
    allowed_deliverables: list[str]
    allowed_channels: list[Channel]
    forbidden_actions: list[str]
    maximum_replies_per_case: int = 4
    maximum_external_deliveries_per_day: int = 20
    maximum_attachment_size_mb: float = 10.0
    minimum_identity_confidence: float = 0.90
    minimum_authority_confidence: float = 0.75
    maximum_data_class: DataClass = DataClass.CLIENT_CONFIDENTIAL
    expires_at: str | None = None
    kill_switch: bool = False


@dataclass(frozen=True, slots=True)
class GateResult:
    case_id: str
    decision: ReplyDecision
    reasons: tuple[str, ...]
    required_approvals: int = 0
    allowed_channels: tuple[Channel, ...] = ()
    allowed_deliverables: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    deliverable_id: str
    primary_channel: Channel
    notification_channel: Channel | None
    destination: str
    reasons: tuple[str, ...]
    access_expires_at: str | None = None
    resharing_allowed: bool = False


@dataclass(slots=True)
class DeliveryReceipt:
    receipt_id: str
    case_id: str
    deliverable_id: str
    channel: Channel
    destination: str
    content_hashes: dict[str, str]
    status: str
    prepared_at: str = field(default_factory=utc_now)
    dispatched_at: str | None = None
    provider_accepted_at: str | None = None
    recipient_confirmed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["channel"] = self.channel.value
        return payload
