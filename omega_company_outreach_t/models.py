from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
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
    SENT = "sent"
    REPLIED = "replied"
    FOLLOW_UP_DUE = "follow_up_due"
    CLOSED = "closed"
    BLOCKED = "blocked"


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


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

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.case_id.startswith("OUT-"):
            errors.append("case_id must start with OUT-")
        if not self.target_organization.strip():
            errors.append("target_organization is required")
        if not self.recipient_hash.startswith("sha256:") or len(self.recipient_hash) != 71:
            errors.append("recipient_hash must be a canonical sha256 value")
        if not self.subject.strip() or len(self.subject) > 180:
            errors.append("subject is required and must be <= 180 characters")
        if not self.purpose.strip():
            errors.append("purpose is required")
        if self.status is OutreachStatus.SENT:
            if not self.sent_at:
                errors.append("sent_at is required for SENT cases")
            if not self.provider_receipt_hash:
                errors.append("provider_receipt_hash is required for SENT cases")
        if self.provider_receipt_hash and (
            not self.provider_receipt_hash.startswith("sha256:")
            or len(self.provider_receipt_hash) != 71
        ):
            errors.append("provider_receipt_hash must be a canonical sha256 value")
        if self.legal_entity_claimed and not self.corporate_domain_verified:
            errors.append("legal entity claims require a verified corporate domain")
        return errors

    def public_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["company_unit"] = self.company_unit.value
        payload["kind"] = self.kind.value
        payload["status"] = self.status.value
        return payload

    @property
    def case_hash(self) -> str:
        canonical = json.dumps(
            self.public_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256_text(canonical)
