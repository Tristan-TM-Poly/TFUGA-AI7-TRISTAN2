"""Corporate identity, authority, compliance, and OAK gates for Ω-MAIL-T.

This module does not constitute or register a company. It verifies evidence
supplied by the operator and decides whether one prepared message may progress
from simulation to a tightly controlled external-send attempt.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class CompanyState(str, Enum):
    IDEA = "IDEA"
    CANDIDATE_BRAND = "CANDIDATE_BRAND"
    INTERNAL_DIVISION = "INTERNAL_DIVISION"
    FOUNDING_PACKET_READY = "FOUNDING_PACKET_READY"
    FILING_SUBMITTED = "FILING_SUBMITTED"
    REGISTERED = "REGISTERED"
    INCORPORATED = "INCORPORATED"
    DOMAIN_VERIFIED = "DOMAIN_VERIFIED"
    MAIL_AUTHENTICATED = "MAIL_AUTHENTICATED"
    PRODUCTION_AUTHORIZED = "PRODUCTION_AUTHORIZED"


LEGAL_STATES = frozenset(
    {
        CompanyState.REGISTERED,
        CompanyState.INCORPORATED,
        CompanyState.DOMAIN_VERIFIED,
        CompanyState.MAIL_AUTHENTICATED,
        CompanyState.PRODUCTION_AUTHORIZED,
    }
)


class MessageClass(str, Enum):
    E0_SIMULATION = "E0_SIMULATION"
    E1_CONTROLLED_TEST = "E1_CONTROLLED_TEST"
    E2_PREINCORPORATION_INQUIRY = "E2_PREINCORPORATION_INQUIRY"
    E3_OFFICIAL_NONCOMMERCIAL = "E3_OFFICIAL_NONCOMMERCIAL"
    E4_INDIVIDUAL_COMMERCIAL = "E4_INDIVIDUAL_COMMERCIAL"
    E5_COMMERCIAL_CAMPAIGN = "E5_COMMERCIAL_CAMPAIGN"


class OfficialDecision(str, Enum):
    ALLOW_DRY_RUN = "ALLOW_DRY_RUN"
    ALLOW_ONE_MESSAGE = "ALLOW_ONE_MESSAGE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class CompanyIdentity:
    company_id: str
    conceptual_name: str
    state: CompanyState = CompanyState.IDEA
    legal_name: str | None = None
    operating_name: str | None = None
    jurisdiction: str | None = None
    neq: str | None = None
    corporation_number: str | None = None
    domain: str | None = None
    legal_identity_verified: bool = False
    domain_control_verified: bool = False
    spf_verified: bool = False
    dkim_verified: bool = False
    dmarc_verified: bool = False
    external_send_enabled: bool = False
    evidence_ids: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CompanyIdentity":
        return cls(
            company_id=str(data["company_id"]),
            conceptual_name=str(data["conceptual_name"]),
            state=CompanyState(str(data.get("state", CompanyState.IDEA.value))),
            legal_name=_optional_text(data.get("legal_name")),
            operating_name=_optional_text(data.get("operating_name")),
            jurisdiction=_optional_text(data.get("jurisdiction")),
            neq=_optional_text(data.get("neq")),
            corporation_number=_optional_text(data.get("corporation_number")),
            domain=_optional_text(data.get("domain")),
            legal_identity_verified=bool(data.get("legal_identity_verified", False)),
            domain_control_verified=bool(data.get("domain_control_verified", False)),
            spf_verified=bool(data.get("spf_verified", False)),
            dkim_verified=bool(data.get("dkim_verified", False)),
            dmarc_verified=bool(data.get("dmarc_verified", False)),
            external_send_enabled=bool(data.get("external_send_enabled", False)),
            evidence_ids=tuple(str(v) for v in data.get("evidence_ids", ())),
        )


@dataclass(frozen=True, slots=True)
class MailAuthority:
    identity: str
    mailbox: str
    permissions: tuple[str, ...] = ()
    active: bool = True
    valid_until: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "MailAuthority":
        return cls(
            identity=str(data["identity"]),
            mailbox=_normalize_address(str(data["mailbox"])),
            permissions=tuple(sorted({str(v) for v in data.get("permissions", ())})),
            active=bool(data.get("active", True)),
            valid_until=_optional_text(data.get("valid_until")),
        )

    def permits(self, permission: str, *, now: datetime | None = None) -> bool:
        if not self.active or permission not in self.permissions:
            return False
        if not self.valid_until:
            return True
        instant = now or datetime.now(timezone.utc)
        try:
            expiry = datetime.fromisoformat(self.valid_until.replace("Z", "+00:00"))
        except ValueError:
            return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return instant <= expiry


@dataclass(frozen=True, slots=True)
class ComplianceContext:
    message_class: MessageClass
    commercial: bool = False
    consent_basis: str | None = None
    consent_evidence_id: str | None = None
    sender_identified: bool = False
    contact_information_present: bool = False
    unsubscribe_present: bool = False
    contains_personal_information: bool = False
    privacy_reviewed: bool = False
    cross_border_transfer: bool = False
    cross_border_assessment_id: str | None = None
    ip_reviewed: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ComplianceContext":
        return cls(
            message_class=MessageClass(str(data["message_class"])),
            commercial=bool(data.get("commercial", False)),
            consent_basis=_optional_text(data.get("consent_basis")),
            consent_evidence_id=_optional_text(data.get("consent_evidence_id")),
            sender_identified=bool(data.get("sender_identified", False)),
            contact_information_present=bool(data.get("contact_information_present", False)),
            unsubscribe_present=bool(data.get("unsubscribe_present", False)),
            contains_personal_information=bool(data.get("contains_personal_information", False)),
            privacy_reviewed=bool(data.get("privacy_reviewed", False)),
            cross_border_transfer=bool(data.get("cross_border_transfer", False)),
            cross_border_assessment_id=_optional_text(data.get("cross_border_assessment_id")),
            ip_reviewed=bool(data.get("ip_reviewed", False)),
        )


@dataclass(frozen=True, slots=True)
class OfficialMessageDraft:
    sender: str
    recipients: tuple[str, ...]
    subject: str
    body: str
    attachments: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OfficialMessageDraft":
        recipients = tuple(_normalize_address(str(v)) for v in data.get("recipients", ()))
        return cls(
            sender=_normalize_address(str(data["sender"])),
            recipients=recipients,
            subject=str(data.get("subject", "")).strip(),
            body=str(data.get("body", "")),
            attachments=tuple(str(v) for v in data.get("attachments", ())),
            metadata=dict(data.get("metadata", {})),
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipients": list(self.recipients),
            "subject": self.subject,
            "body": self.body,
            "attachments": list(self.attachments),
            "metadata": _canonicalize(self.metadata),
        }

    @property
    def content_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    message_hash: str
    approver: str
    approved_at: str
    scope: str = "ONE_MESSAGE"
    note: str = ""

    @classmethod
    def create(
        cls,
        draft: OfficialMessageDraft,
        *,
        approver: str,
        note: str = "",
        approved_at: datetime | None = None,
    ) -> "ApprovalRecord":
        instant = approved_at or datetime.now(timezone.utc)
        return cls(
            message_hash=draft.content_hash,
            approver=approver.strip(),
            approved_at=instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            note=note,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApprovalRecord":
        return cls(
            message_hash=str(data["message_hash"]),
            approver=str(data["approver"]),
            approved_at=str(data["approved_at"]),
            scope=str(data.get("scope", "ONE_MESSAGE")),
            note=str(data.get("note", "")),
        )

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OfficialGateReport:
    decision: OfficialDecision
    reasons: tuple[str, ...]
    checks: Mapping[str, bool]
    message_hash: str

    @property
    def allowed(self) -> bool:
        return self.decision in {
            OfficialDecision.ALLOW_DRY_RUN,
            OfficialDecision.ALLOW_ONE_MESSAGE,
        }

    def to_mapping(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
            "message_hash": self.message_hash,
        }


class OfficializationGate:
    """Evaluate one message against legal, technical, authority, and policy evidence."""

    def evaluate(
        self,
        *,
        company: CompanyIdentity,
        draft: OfficialMessageDraft,
        authority: MailAuthority,
        compliance: ComplianceContext,
        approval: ApprovalRecord | None = None,
        production: bool = False,
    ) -> OfficialGateReport:
        checks: dict[str, bool] = {}
        reasons: list[str] = []

        def check(name: str, passed: bool, reason: str) -> None:
            checks[name] = passed
            if not passed:
                reasons.append(reason)

        check("sender_present", bool(draft.sender), "missing_sender")
        check("recipient_present", len(draft.recipients) > 0, "missing_recipient")
        check("subject_present", bool(draft.subject), "missing_subject")
        check("body_present", bool(draft.body.strip()), "missing_body")
        check(
            "single_recipient",
            len(draft.recipients) == 1,
            "production_send_requires_exactly_one_recipient",
        )
        check(
            "no_campaign",
            compliance.message_class != MessageClass.E5_COMMERCIAL_CAMPAIGN,
            "campaign_mode_not_supported",
        )

        domain = draft.sender.rsplit("@", 1)[1] if "@" in draft.sender else ""
        check(
            "sender_domain_matches",
            bool(company.domain) and domain.casefold() == company.domain.casefold(),
            "sender_domain_mismatch",
        )
        check(
            "authority_mailbox_matches",
            draft.sender == authority.mailbox,
            "authority_mailbox_mismatch",
        )
        check(
            "authority_active",
            authority.permits("send_external"),
            "sender_not_authorized_for_external_mail",
        )

        if production:
            check("legal_state", company.state in LEGAL_STATES, "company_not_legally_registered")
            check(
                "legal_identity_verified",
                company.legal_identity_verified and bool(company.legal_name),
                "legal_identity_not_verified",
            )
            check("domain_control_verified", company.domain_control_verified, "domain_control_not_verified")
            check("spf_verified", company.spf_verified, "spf_not_verified")
            check("dkim_verified", company.dkim_verified, "dkim_not_verified")
            check("dmarc_verified", company.dmarc_verified, "dmarc_not_verified")
            check("external_send_enabled", company.external_send_enabled, "external_send_disabled")
        else:
            checks.update(
                {
                    "legal_state": company.state in LEGAL_STATES,
                    "legal_identity_verified": company.legal_identity_verified and bool(company.legal_name),
                    "domain_control_verified": company.domain_control_verified,
                    "spf_verified": company.spf_verified,
                    "dkim_verified": company.dkim_verified,
                    "dmarc_verified": company.dmarc_verified,
                    "external_send_enabled": company.external_send_enabled,
                }
            )

        check("sender_identified", compliance.sender_identified, "sender_identification_missing")
        check(
            "contact_information_present",
            compliance.contact_information_present,
            "corporate_contact_information_missing",
        )
        check("ip_reviewed", compliance.ip_reviewed, "ip_review_missing")

        if compliance.commercial:
            check(
                "commercial_class",
                compliance.message_class == MessageClass.E4_INDIVIDUAL_COMMERCIAL,
                "commercial_message_class_invalid",
            )
            check(
                "consent_basis",
                bool(compliance.consent_basis and compliance.consent_evidence_id),
                "commercial_consent_evidence_missing",
            )
            check("unsubscribe_present", compliance.unsubscribe_present, "unsubscribe_mechanism_missing")
        else:
            checks["commercial_class"] = True
            checks["consent_basis"] = True
            checks["unsubscribe_present"] = True

        if compliance.contains_personal_information:
            check("privacy_reviewed", compliance.privacy_reviewed, "privacy_review_missing")
        else:
            checks["privacy_reviewed"] = True

        if compliance.cross_border_transfer:
            check(
                "cross_border_assessment",
                bool(compliance.cross_border_assessment_id),
                "cross_border_privacy_assessment_missing",
            )
        else:
            checks["cross_border_assessment"] = True

        if production:
            if approval is None:
                reasons.append("human_approval_missing")
                checks["human_approval"] = False
            else:
                approval_ok = (
                    approval.scope == "ONE_MESSAGE"
                    and bool(approval.approver.strip())
                    and approval.message_hash == draft.content_hash
                )
                check("human_approval", approval_ok, "approval_hash_or_scope_mismatch")
        else:
            checks["human_approval"] = approval is not None and approval.message_hash == draft.content_hash

        if reasons:
            decision = (
                OfficialDecision.REQUIRE_APPROVAL
                if production and reasons == ["human_approval_missing"]
                else OfficialDecision.BLOCK
            )
        else:
            decision = OfficialDecision.ALLOW_ONE_MESSAGE if production else OfficialDecision.ALLOW_DRY_RUN

        return OfficialGateReport(
            decision=decision,
            reasons=tuple(reasons),
            checks=checks,
            message_hash=draft.content_hash,
        )


def _normalize_address(value: str) -> str:
    address = value.strip().casefold()
    if address.count("@") != 1:
        raise ValueError(f"invalid email address: {value!r}")
    local, domain = address.split("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError(f"invalid email address: {value!r}")
    return address


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(k): _canonicalize(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
