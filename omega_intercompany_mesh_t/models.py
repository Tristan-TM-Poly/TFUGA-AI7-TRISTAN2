from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class LegalStatus(str, Enum):
    CONCEPT = "CONCEPT"
    INTERNAL_DIVISION = "INTERNAL_DIVISION"
    CANDIDATE_ENTITY = "CANDIDATE_ENTITY"
    REGISTERED_ENTITY = "REGISTERED_ENTITY"


class AgreementFamily(str, Enum):
    OPERATING_CHARTER = "OPERATING_CHARTER"
    SHARED_SERVICES = "SHARED_SERVICES"
    IP_LICENSE = "IP_LICENSE"
    DATA_PRIVACY = "DATA_PRIVACY"
    DELIVERY_SLA = "DELIVERY_SLA"
    INVOICING = "INVOICING"
    SECURITY_COOPERATION = "SECURITY_COOPERATION"


class PacketStatus(str, Enum):
    DRAFT_NON_BINDING = "DRAFT_NON_BINDING"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    SIGNATURE_REQUIRED = "SIGNATURE_REQUIRED"
    ACTIVE_VERIFIED = "ACTIVE_VERIFIED"


@dataclass(frozen=True, slots=True)
class CompanyNode:
    company_id: str
    display_name: str
    legal_status: LegalStatus
    role: str
    mailbox_placeholder: str


@dataclass(slots=True)
class AgreementPacket:
    packet_id: str
    source_company_id: str
    destination_company_id: str
    family: AgreementFamily
    title: str
    clauses: list[str]
    status: PacketStatus = PacketStatus.DRAFT_NON_BINDING
    legal_names_verified: bool = False
    human_approval_required: bool = True
    professional_review_required: bool = True
    content_hash: str | None = None

    def seal(self) -> str:
        payload = asdict(self)
        payload["family"] = self.family.value
        payload["status"] = self.status.value
        payload["content_hash"] = None
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.content_hash = sha256(canonical.encode("utf-8")).hexdigest()
        return self.content_hash

    def to_dict(self) -> dict[str, Any]:
        if not self.content_hash:
            self.seal()
        payload = asdict(self)
        payload["family"] = self.family.value
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class MailPacket:
    mail_id: str
    thread_id: str
    source_company_id: str
    destination_company_id: str
    stage: str
    subject: str
    body: str
    agreement_packet_ids: tuple[str, ...] = ()
    auto_reply: bool = False
    external_send_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
