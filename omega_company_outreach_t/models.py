from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import hmac
import json
from typing import Any


class CompanyUnit(str, Enum):
    PARENT = "tristan_parent_opco"
    OAK = "tristan_oak_systems"
    SOFTWARE = "tristan_software_labs"
    RESEARCH = "tristan_research_foundry"


class OutreachKind(str, Enum):
    ENTREPRENEURSHIP = "entrepreneurship"
    PARTNERSHIP = "partnership"
    SOFTWARE_PILOT = "software_pilot"
    RESEARCH_PILOT = "research_pilot"
    GOVERNANCE = "governance"
    SUPPORT = "support"


class OutreachStatus(str, Enum):
    PREPARED = "prepared"
    APPROVED = "approved"
    SENT = "sent"
    DELIVERED = "delivered"
    REPLIED = "replied"
    WAITING = "waiting"
    FOLLOW_UP_DUE = "follow_up_due"
    CLOSED = "closed"
    BLOCKED = "blocked"


class ConsentBasis(str, Enum):
    EXPRESS = "express"
    EXISTING_BUSINESS_RELATIONSHIP = "existing_business_relationship"
    EXISTING_NON_BUSINESS_RELATIONSHIP = "existing_non_business_relationship"
    PUBLIC_INSTITUTIONAL_CONTACT = "public_institutional_contact"
    INQUIRY_RESPONSE = "inquiry_response"
    NOT_COMMERCIAL = "not_commercial"
    NONE = "none"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReplyClass(str, Enum):
    POSITIVE = "positive"
    INFORMATION_REQUEST = "information_request"
    REFERRAL = "referral"
    AUTO_REPLY = "auto_reply"
    DECLINE = "decline"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"
    UNKNOWN = "unknown"


class MailEventType(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    REPLY = "reply"
    AUTO_REPLY = "auto_reply"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"


class NextAction(str, Enum):
    WAIT = "wait"
    PREPARE_MEETING = "prepare_meeting"
    PREPARE_EVIDENCE = "prepare_evidence"
    REVIEW_REFERRAL = "review_referral"
    CORRECT_ADDRESS = "correct_address"
    CLOSE = "close"
    HUMAN_REVIEW = "human_review"
    FOLLOW_UP = "follow_up"
    BLOCK = "block"


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def hmac_sha256_text(value: str, secret: str) -> str:
    if len(secret) < 16:
        raise ValueError("hash secret must contain at least 16 characters")
    return "hmac-sha256:" + hmac.new(
        secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def is_public_hash(value: str | None) -> bool:
    if not value:
        return False
    if value.startswith("sha256:"):
        return len(value) == 71
    if value.startswith("hmac-sha256:"):
        return len(value) == 76
    return False


@dataclass(frozen=True, slots=True)
class OutreachCase:
    case_id: str
    company_unit: CompanyUnit
    kind: OutreachKind
    target_organization: str
    recipient_hash: str
    subject: str
    purpose: str
    status: OutreachStatus
    sent_at: str | None = None
    provider_receipt_hash: str | None = None
    source_issue: int | None = None
    follow_up_after: str | None = None
    legal_entity_claimed: bool = False
    corporate_domain_verified: bool = False
    consent_basis: ConsentBasis = ConsentBasis.NOT_COMMERCIAL
    commercial_message: bool = False
    unsubscribe_required: bool = False
    unsubscribe_mechanism_verified: bool = False
    sender_identity_verified: bool = True
    thread_hash: str | None = None
    latest_event_at: str | None = None
    reply_class: ReplyClass | None = None
    risk_tier: RiskTier = RiskTier.LOW

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.case_id.startswith("OUT-"):
            errors.append("case_id must start with OUT-")
        if not self.target_organization.strip():
            errors.append("target_organization is required")
        if not is_public_hash(self.recipient_hash):
            errors.append("recipient_hash must be a canonical public hash")
        if not self.subject.strip() or len(self.subject) > 180:
            errors.append("subject is required and must be <= 180 characters")
        if not self.purpose.strip():
            errors.append("purpose is required")
        if self.status in {
            OutreachStatus.SENT,
            OutreachStatus.DELIVERED,
            OutreachStatus.REPLIED,
            OutreachStatus.WAITING,
            OutreachStatus.FOLLOW_UP_DUE,
            OutreachStatus.CLOSED,
        }:
            if not self.sent_at:
                errors.append("sent_at is required after sending")
            if not self.provider_receipt_hash:
                errors.append("provider_receipt_hash is required after sending")
        if self.provider_receipt_hash and not is_public_hash(self.provider_receipt_hash):
            errors.append("provider_receipt_hash must be a canonical public hash")
        if self.thread_hash and not is_public_hash(self.thread_hash):
            errors.append("thread_hash must be a canonical public hash")
        if self.legal_entity_claimed and not self.corporate_domain_verified:
            errors.append("legal entity claims require a verified corporate domain")
        if self.commercial_message:
            if self.consent_basis is ConsentBasis.NONE:
                errors.append("commercial messages require a consent basis")
            if not self.unsubscribe_required:
                errors.append("commercial messages must require unsubscribe")
            if not self.unsubscribe_mechanism_verified:
                errors.append("commercial messages require a verified unsubscribe mechanism")
        if not self.sender_identity_verified:
            errors.append("sender identity must be verified")
        return errors

    def public_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["company_unit"] = self.company_unit.value
        payload["kind"] = self.kind.value
        payload["status"] = self.status.value
        payload["consent_basis"] = self.consent_basis.value
        payload["risk_tier"] = self.risk_tier.value
        payload["reply_class"] = self.reply_class.value if self.reply_class else None
        return payload

    @property
    def case_hash(self) -> str:
        canonical = json.dumps(
            self.public_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256_text(canonical)


@dataclass(frozen=True, slots=True)
class PublicMailEvent:
    event_id: str
    case_id: str
    event_type: MailEventType
    message_hash: str
    thread_hash: str
    counterparty_hash: str
    occurred_at: str
    provider: str = "gmail"
    reply_class: ReplyClass | None = None
    source_issue: int | None = None
    raw_content_retained: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.event_id.startswith("EVT-"):
            errors.append("event_id must start with EVT-")
        if not self.case_id.startswith("OUT-"):
            errors.append("case_id must start with OUT-")
        for name, value in (
            ("message_hash", self.message_hash),
            ("thread_hash", self.thread_hash),
            ("counterparty_hash", self.counterparty_hash),
        ):
            if not is_public_hash(value):
                errors.append(f"{name} must be a canonical public hash")
        if self.raw_content_retained:
            errors.append("public events must not retain raw content")
        if self.event_type in {
            MailEventType.REPLY,
            MailEventType.AUTO_REPLY,
            MailEventType.BOUNCE,
            MailEventType.UNSUBSCRIBE,
        } and self.reply_class is None:
            errors.append("reply-like events require reply_class")
        return errors

    def public_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["event_type"] = self.event_type.value
        payload["reply_class"] = self.reply_class.value if self.reply_class else None
        return payload

    @property
    def event_hash(self) -> str:
        canonical = json.dumps(
            self.public_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256_text(canonical)


@dataclass(frozen=True, slots=True)
class StrategicSignals:
    relevance: int
    decision_authority: int
    problem_fit: int
    evidence_readiness: int
    timing: int
    reciprocity: int
    effort: int
    risk: int

    def validate(self) -> list[str]:
        errors = []
        for name, value in asdict(self).items():
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{name} must be an integer from 0 to 5")
        return errors


@dataclass(frozen=True, slots=True)
class StrategicScore:
    case_id: str
    score: int
    disposition: str
    reasons: tuple[str, ...]
    next_action: NextAction

    def public_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["next_action"] = self.next_action.value
        payload["reasons"] = list(self.reasons)
        return payload
