from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping

from .canonical import (
    CanonicalizationError,
    canonical_hash,
    ensure_utc,
    is_hmac_sha256,
    is_sha256,
    normalize_domain,
    normalize_text,
    stable_unique,
    utc_now,
    validate_public_identifier,
    validate_vault_reference,
)


class ContactState(str, Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    CONTACTABLE = "contactable"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    INACTIVE = "inactive"
    BOUNCED = "bounced"
    SUPPRESSED = "suppressed"


class ContactSource(str, Enum):
    PUBLIC_DIRECTORY = "public_directory"
    OFFICIAL_WEBSITE = "official_website"
    EXISTING_RELATIONSHIP = "existing_relationship"
    REFERRAL = "referral"
    INBOUND_MESSAGE = "inbound_message"
    CONFERENCE = "conference"
    PROFESSIONAL_NETWORK = "professional_network"
    HUMAN_ENTRY = "human_entry"


class RoleCategory(str, Enum):
    EXECUTIVE = "executive"
    FOUNDER = "founder"
    PROGRAM_MANAGER = "program_manager"
    RESEARCH_DIRECTOR = "research_director"
    PROFESSOR = "professor"
    ENGINEER = "engineer"
    SECURITY = "security"
    PROCUREMENT = "procurement"
    FINANCE = "finance"
    LEGAL = "legal"
    PRIVACY = "privacy"
    SUPPORT = "support"
    GENERAL_INBOX = "general_inbox"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContactEvidence:
    evidence_id: str
    source: ContactSource
    source_hash: str
    observed_at: datetime
    organization_domain: str | None = None
    role_verified: bool = False
    relationship_verified: bool = False
    confidence: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            validate_public_identifier(self.evidence_id, prefix="EVID"),
        )
        if not is_sha256(self.source_hash):
            raise CanonicalizationError("contact evidence source_hash must be canonical SHA-256")
        if not 0 <= self.confidence <= 1:
            raise CanonicalizationError("contact evidence confidence must be between 0 and 1")
        if self.organization_domain:
            object.__setattr__(
                self, "organization_domain", normalize_domain(self.organization_domain)
            )
        object.__setattr__(self, "observed_at", ensure_utc(self.observed_at))

    @property
    def evidence_hash(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class ContactPreferences:
    language: str = "fr"
    preferred_channel: str = "email"
    no_marketing: bool = False
    no_follow_up: bool = False
    no_attachments: bool = False
    maximum_messages_per_30_days: int = 2
    notes_hash: str | None = None

    def __post_init__(self) -> None:
        language = normalize_text(self.language).casefold()
        if language not in {"fr", "en", "fr-ca", "en-ca"}:
            raise CanonicalizationError("unsupported contact language")
        channel = normalize_text(self.preferred_channel).casefold()
        if channel not in {"email", "calendar", "portal", "none"}:
            raise CanonicalizationError("unsupported preferred channel")
        if not 0 <= self.maximum_messages_per_30_days <= 20:
            raise CanonicalizationError("maximum_messages_per_30_days must be between 0 and 20")
        if self.notes_hash is not None and not is_sha256(self.notes_hash):
            raise CanonicalizationError("notes_hash must be canonical SHA-256")
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "preferred_channel", channel)


@dataclass(frozen=True, slots=True)
class ContactRecord:
    contact_id: str
    organization_id: str
    role_category: RoleCategory
    state: ContactState
    recipient_hash: str
    private_email_ref: str
    private_name_ref: str | None = None
    title: str | None = None
    department: str | None = None
    domain: str | None = None
    sources: tuple[ContactEvidence, ...] = ()
    preferences: ContactPreferences = field(default_factory=ContactPreferences)
    tags: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "contact_id",
            validate_public_identifier(self.contact_id, prefix="CNT"),
        )
        object.__setattr__(
            self,
            "organization_id",
            validate_public_identifier(self.organization_id, prefix="ORG"),
        )
        if not (is_hmac_sha256(self.recipient_hash) or is_sha256(self.recipient_hash)):
            raise CanonicalizationError("recipient_hash must be SHA-256 or HMAC-SHA-256")
        object.__setattr__(
            self, "private_email_ref", validate_vault_reference(self.private_email_ref)
        )
        if self.private_name_ref:
            object.__setattr__(
                self, "private_name_ref", validate_vault_reference(self.private_name_ref)
            )
        title = normalize_text(self.title) if self.title else None
        department = normalize_text(self.department) if self.department else None
        if title and len(title) > 240:
            raise CanonicalizationError("contact title is too long")
        if department and len(department) > 240:
            raise CanonicalizationError("contact department is too long")
        domain = normalize_domain(self.domain) if self.domain else None
        source_ids = [source.evidence_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise CanonicalizationError("duplicate contact evidence IDs")
        created_at = ensure_utc(self.created_at)
        updated_at = ensure_utc(self.updated_at)
        if updated_at < created_at:
            raise CanonicalizationError("contact updated_at cannot precede created_at")
        if self.state in {ContactState.VERIFIED, ContactState.CONTACTABLE, ContactState.CONTACTED, ContactState.ENGAGED}:
            if not self.sources:
                raise CanonicalizationError("verified/contactable contacts require evidence")
        if self.state is ContactState.SUPPRESSED and not self.preferences.no_follow_up:
            raise CanonicalizationError("suppressed contact must set no_follow_up")
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "department", department)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "tags", stable_unique(self.tags))
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    @property
    def contact_hash(self) -> str:
        return canonical_hash(self)

    @property
    def evidence_confidence(self) -> float:
        if not self.sources:
            return 0.0
        weighted = sum(
            source.confidence
            * (1.20 if source.role_verified else 1.0)
            * (1.15 if source.relationship_verified else 1.0)
            for source in self.sources
        )
        denominator = sum(
            (1.20 if source.role_verified else 1.0)
            * (1.15 if source.relationship_verified else 1.0)
            for source in self.sources
        )
        return min(1.0, weighted / denominator)

    @property
    def professionally_verified(self) -> bool:
        return any(source.role_verified for source in self.sources) and self.evidence_confidence >= 0.65

    def can_be_contacted(self) -> bool:
        return (
            self.state in {ContactState.CONTACTABLE, ContactState.CONTACTED, ContactState.ENGAGED}
            and not self.preferences.no_follow_up
            and self.preferences.preferred_channel != "none"
            and self.preferences.maximum_messages_per_30_days > 0
        )

    def transition(self, target: ContactState, *, now: datetime | None = None) -> "ContactRecord":
        allowed = {
            ContactState.DISCOVERED: frozenset(
                {ContactState.VERIFIED, ContactState.INACTIVE, ContactState.SUPPRESSED}
            ),
            ContactState.VERIFIED: frozenset(
                {ContactState.CONTACTABLE, ContactState.INACTIVE, ContactState.SUPPRESSED}
            ),
            ContactState.CONTACTABLE: frozenset(
                {
                    ContactState.CONTACTED,
                    ContactState.INACTIVE,
                    ContactState.BOUNCED,
                    ContactState.SUPPRESSED,
                }
            ),
            ContactState.CONTACTED: frozenset(
                {
                    ContactState.ENGAGED,
                    ContactState.INACTIVE,
                    ContactState.BOUNCED,
                    ContactState.SUPPRESSED,
                }
            ),
            ContactState.ENGAGED: frozenset(
                {ContactState.CONTACTED, ContactState.INACTIVE, ContactState.SUPPRESSED}
            ),
            ContactState.INACTIVE: frozenset(
                {ContactState.VERIFIED, ContactState.SUPPRESSED}
            ),
            ContactState.BOUNCED: frozenset(
                {ContactState.VERIFIED, ContactState.INACTIVE, ContactState.SUPPRESSED}
            ),
            ContactState.SUPPRESSED: frozenset(),
        }
        if target not in allowed[self.state]:
            raise CanonicalizationError(
                f"contact transition {self.state.value} -> {target.value} is forbidden"
            )
        preferences = self.preferences
        if target is ContactState.SUPPRESSED:
            preferences = replace(preferences, no_follow_up=True, preferred_channel="none")
        return replace(self, state=target, preferences=preferences, updated_at=now or utc_now())

    def with_evidence(self, evidence: ContactEvidence, *, now: datetime | None = None) -> "ContactRecord":
        if any(item.evidence_id == evidence.evidence_id for item in self.sources):
            raise CanonicalizationError(f"duplicate evidence_id: {evidence.evidence_id}")
        return replace(self, sources=tuple((*self.sources, evidence)), updated_at=now or utc_now())


@dataclass(frozen=True, slots=True)
class ContactDuplicateCandidate:
    left_id: str
    right_id: str
    confidence: float
    reasons: tuple[str, ...]


def contact_similarity(left: ContactRecord, right: ContactRecord) -> ContactDuplicateCandidate:
    score = 0.0
    reasons: list[str] = []
    if left.contact_id == right.contact_id:
        return ContactDuplicateCandidate(left.contact_id, right.contact_id, 1.0, ("contact_id",))
    if left.recipient_hash == right.recipient_hash:
        score += 0.75
        reasons.append("recipient_hash")
    if left.organization_id == right.organization_id:
        score += 0.10
        reasons.append("organization")
    if left.domain and right.domain and left.domain == right.domain:
        score += 0.05
        reasons.append("domain")
    if left.role_category is right.role_category and left.role_category is not RoleCategory.UNKNOWN:
        score += 0.05
        reasons.append("role")
    if left.private_name_ref and left.private_name_ref == right.private_name_ref:
        score += 0.15
        reasons.append("private_name_ref")
    return ContactDuplicateCandidate(
        left_id=left.contact_id,
        right_id=right.contact_id,
        confidence=min(1.0, round(score, 6)),
        reasons=tuple(reasons),
    )


def find_contact_duplicates(
    contacts: Iterable[ContactRecord], *, threshold: float = 0.75
) -> tuple[ContactDuplicateCandidate, ...]:
    if not 0 <= threshold <= 1:
        raise CanonicalizationError("contact duplicate threshold must be between 0 and 1")
    materialized = tuple(contacts)
    candidates: list[ContactDuplicateCandidate] = []
    for index, left in enumerate(materialized):
        for right in materialized[index + 1 :]:
            candidate = contact_similarity(left, right)
            if candidate.confidence >= threshold:
                candidates.append(candidate)
    return tuple(sorted(candidates, key=lambda item: (-item.confidence, item.left_id, item.right_id)))


def audit_contact(contact: ContactRecord) -> list[str]:
    errors: list[str] = []
    if contact.state is ContactState.CONTACTABLE and not contact.professionally_verified:
        errors.append("contactable contact lacks sufficient professional evidence")
    if contact.domain and contact.sources:
        source_domains = {source.organization_domain for source in contact.sources if source.organization_domain}
        if source_domains and contact.domain not in source_domains:
            errors.append("contact domain is inconsistent with evidence")
    if contact.role_category is RoleCategory.UNKNOWN and contact.state not in {
        ContactState.DISCOVERED,
        ContactState.INACTIVE,
        ContactState.SUPPRESSED,
    }:
        errors.append("active contact cannot keep an unknown role")
    return errors


def audit_contacts(contacts: Iterable[ContactRecord]) -> list[str]:
    materialized = tuple(contacts)
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_recipients: dict[str, str] = {}
    for contact in materialized:
        if contact.contact_id in seen_ids:
            errors.append(f"duplicate contact_id: {contact.contact_id}")
        seen_ids.add(contact.contact_id)
        if contact.recipient_hash in seen_recipients:
            errors.append(
                f"duplicate recipient hash: {contact.contact_id} and {seen_recipients[contact.recipient_hash]}"
            )
        else:
            seen_recipients[contact.recipient_hash] = contact.contact_id
        errors.extend(f"{contact.contact_id}: {error}" for error in audit_contact(contact))
    for candidate in find_contact_duplicates(materialized):
        if "recipient_hash" not in candidate.reasons:
            errors.append(
                f"probable contact duplicate: {candidate.left_id} / {candidate.right_id} "
                f"({candidate.confidence:.3f})"
            )
    return errors
