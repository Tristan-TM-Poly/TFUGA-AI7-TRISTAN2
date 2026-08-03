from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping

from .canonical import (
    CanonicalizationError,
    canonical_hash,
    ensure_utc,
    is_sha256,
    normalize_text,
    stable_unique,
    utc_now,
    validate_public_identifier,
)


class ConsentBasis(str, Enum):
    EXPRESS = "express"
    EXISTING_BUSINESS_RELATIONSHIP = "existing_business_relationship"
    EXISTING_NONBUSINESS_RELATIONSHIP = "existing_nonbusiness_relationship"
    CONSPICUOUSLY_PUBLISHED_BUSINESS_CONTACT = "conspicuously_published_business_contact"
    INBOUND_REQUEST = "inbound_request"
    REFERRAL = "referral"
    TRANSACTIONAL_NECESSITY = "transactional_necessity"
    LEGITIMATE_PROFESSIONAL_CONTEXT = "legitimate_professional_context"
    NONE = "none"


class ConsentScope(str, Enum):
    DIRECT_INDIVIDUAL_CONTACT = "direct_individual_contact"
    REPLY_TO_REQUEST = "reply_to_request"
    PROGRAM_INFORMATION = "program_information"
    RESEARCH_COLLABORATION = "research_collaboration"
    SOFTWARE_PILOT = "software_pilot"
    STRATEGIC_PARTNERSHIP = "strategic_partnership"
    SUPPORT = "support"
    COMMERCIAL_MARKETING = "commercial_marketing"
    EVENT_INVITATION = "event_invitation"
    TRANSACTIONAL = "transactional"


class ConsentState(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    DENIED = "denied"
    SUPPRESSED = "suppressed"


class SuppressionReason(str, Enum):
    UNSUBSCRIBE = "unsubscribe"
    EXPLICIT_REQUEST = "explicit_request"
    BOUNCE = "bounce"
    ABUSE_COMPLAINT = "abuse_complaint"
    PRIVACY_REQUEST = "privacy_request"
    LEGAL_HOLD = "legal_hold"
    ORGANIZATION_POLICY = "organization_policy"
    DUPLICATE_CONTACT = "duplicate_contact"
    HUMAN_DECISION = "human_decision"


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    consent_id: str
    contact_id: str
    basis: ConsentBasis
    scopes: frozenset[ConsentScope]
    state: ConsentState
    obtained_at: datetime
    evidence_hash: str
    expires_at: datetime | None = None
    withdrawn_at: datetime | None = None
    notes_hash: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "consent_id",
            validate_public_identifier(self.consent_id, prefix="CONSENT"),
        )
        object.__setattr__(
            self,
            "contact_id",
            validate_public_identifier(self.contact_id, prefix="CNT"),
        )
        if not self.scopes:
            raise CanonicalizationError("consent record requires at least one scope")
        if self.basis is ConsentBasis.NONE and self.state is ConsentState.VALID:
            raise CanonicalizationError("consent basis NONE cannot be valid")
        if not is_sha256(self.evidence_hash):
            raise CanonicalizationError("consent evidence_hash must be canonical SHA-256")
        if self.notes_hash is not None and not is_sha256(self.notes_hash):
            raise CanonicalizationError("consent notes_hash must be canonical SHA-256")
        obtained_at = ensure_utc(self.obtained_at)
        expires_at = ensure_utc(self.expires_at) if self.expires_at else None
        withdrawn_at = ensure_utc(self.withdrawn_at) if self.withdrawn_at else None
        if expires_at and expires_at <= obtained_at:
            raise CanonicalizationError("consent expiration must be after obtained_at")
        if withdrawn_at and withdrawn_at < obtained_at:
            raise CanonicalizationError("consent withdrawal cannot precede obtained_at")
        if self.state in {ConsentState.WITHDRAWN, ConsentState.SUPPRESSED} and withdrawn_at is None:
            raise CanonicalizationError("withdrawn/suppressed consent requires withdrawn_at")
        object.__setattr__(self, "obtained_at", obtained_at)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "withdrawn_at", withdrawn_at)
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    @property
    def consent_hash(self) -> str:
        return canonical_hash(self)

    def effective_state(self, moment: datetime | None = None) -> ConsentState:
        current = ensure_utc(moment or utc_now())
        if self.state is ConsentState.VALID and self.expires_at and current > self.expires_at:
            return ConsentState.EXPIRED
        return self.state

    def allows(self, scope: ConsentScope, moment: datetime | None = None) -> bool:
        return self.effective_state(moment) is ConsentState.VALID and scope in self.scopes

    def withdraw(self, *, at: datetime | None = None) -> "ConsentRecord":
        current = ensure_utc(at or utc_now())
        if current < self.obtained_at:
            raise CanonicalizationError("consent cannot be withdrawn before it was obtained")
        return replace(self, state=ConsentState.WITHDRAWN, withdrawn_at=current)


@dataclass(frozen=True, slots=True)
class SuppressionEntry:
    suppression_id: str
    contact_id: str
    reason: SuppressionReason
    created_at: datetime
    evidence_hash: str
    permanent: bool = True
    expires_at: datetime | None = None
    organization_id: str | None = None
    scopes: frozenset[ConsentScope] = frozenset(ConsentScope)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "suppression_id",
            validate_public_identifier(self.suppression_id, prefix="SUPPRESS"),
        )
        object.__setattr__(
            self,
            "contact_id",
            validate_public_identifier(self.contact_id, prefix="CNT"),
        )
        if self.organization_id:
            object.__setattr__(
                self,
                "organization_id",
                validate_public_identifier(self.organization_id, prefix="ORG"),
            )
        if not is_sha256(self.evidence_hash):
            raise CanonicalizationError("suppression evidence_hash must be canonical SHA-256")
        created_at = ensure_utc(self.created_at)
        expires_at = ensure_utc(self.expires_at) if self.expires_at else None
        if self.permanent and expires_at is not None:
            raise CanonicalizationError("permanent suppression cannot expire")
        if not self.permanent:
            if expires_at is None:
                raise CanonicalizationError("temporary suppression requires expires_at")
            if expires_at <= created_at:
                raise CanonicalizationError("suppression expires_at must be after created_at")
        if not self.scopes:
            raise CanonicalizationError("suppression requires at least one scope")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "expires_at", expires_at)

    @property
    def suppression_hash(self) -> str:
        return canonical_hash(self)

    def active_at(self, moment: datetime | None = None) -> bool:
        current = ensure_utc(moment or utc_now())
        return self.permanent or (self.expires_at is not None and current <= self.expires_at)

    def blocks(self, scope: ConsentScope, moment: datetime | None = None) -> bool:
        return self.active_at(moment) and scope in self.scopes


@dataclass(frozen=True, slots=True)
class CommunicationPolicy:
    policy_id: str
    scope: ConsentScope
    requires_express_consent: bool
    permitted_bases: frozenset[ConsentBasis]
    identification_required: bool = True
    unsubscribe_required: bool = False
    maximum_messages_per_30_days: int = 2
    cooldown_days: int = 14
    human_approval_required: bool = True
    allowed_languages: tuple[str, ...] = ("fr", "en")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            validate_public_identifier(self.policy_id, prefix="POLICY"),
        )
        if not self.permitted_bases:
            raise CanonicalizationError("communication policy requires permitted consent bases")
        if self.requires_express_consent and self.permitted_bases != frozenset({ConsentBasis.EXPRESS}):
            raise CanonicalizationError(
                "express-consent policy must permit only the EXPRESS basis"
            )
        if not 0 <= self.maximum_messages_per_30_days <= 31:
            raise CanonicalizationError("maximum_messages_per_30_days must be between 0 and 31")
        if not 0 <= self.cooldown_days <= 365:
            raise CanonicalizationError("cooldown_days must be between 0 and 365")
        languages = stable_unique(tuple(language.casefold() for language in self.allowed_languages))
        if not languages:
            raise CanonicalizationError("communication policy requires allowed languages")
        object.__setattr__(self, "allowed_languages", languages)


@dataclass(frozen=True, slots=True)
class ConsentDecision:
    allowed: bool
    scope: ConsentScope
    basis: ConsentBasis | None
    policy_id: str
    reasons: tuple[str, ...]
    consent_hashes: tuple[str, ...]
    suppression_hashes: tuple[str, ...]

    @property
    def decision_hash(self) -> str:
        return canonical_hash(self)


def resolve_consent(
    contact_id: str,
    scope: ConsentScope,
    policy: CommunicationPolicy,
    *,
    records: Iterable[ConsentRecord],
    suppressions: Iterable[SuppressionEntry] = (),
    moment: datetime | None = None,
) -> ConsentDecision:
    normalized_contact_id = validate_public_identifier(contact_id, prefix="CNT")
    if scope is not policy.scope:
        raise CanonicalizationError("consent scope does not match communication policy")
    current = ensure_utc(moment or utc_now())
    active_suppressions = tuple(
        entry
        for entry in suppressions
        if entry.contact_id == normalized_contact_id and entry.blocks(scope, current)
    )
    if active_suppressions:
        return ConsentDecision(
            allowed=False,
            scope=scope,
            basis=None,
            policy_id=policy.policy_id,
            reasons=("active suppression",),
            consent_hashes=(),
            suppression_hashes=tuple(entry.suppression_hash for entry in active_suppressions),
        )
    matching = tuple(
        record
        for record in records
        if record.contact_id == normalized_contact_id
        and record.allows(scope, current)
        and record.basis in policy.permitted_bases
    )
    if not matching:
        return ConsentDecision(
            allowed=False,
            scope=scope,
            basis=None,
            policy_id=policy.policy_id,
            reasons=("no active consent record for policy and scope",),
            consent_hashes=(),
            suppression_hashes=(),
        )
    selected = sorted(
        matching,
        key=lambda record: (
            record.basis is ConsentBasis.EXPRESS,
            record.obtained_at,
            record.consent_id,
        ),
        reverse=True,
    )[0]
    if policy.requires_express_consent and selected.basis is not ConsentBasis.EXPRESS:
        return ConsentDecision(
            allowed=False,
            scope=scope,
            basis=selected.basis,
            policy_id=policy.policy_id,
            reasons=("express consent required",),
            consent_hashes=tuple(record.consent_hash for record in matching),
            suppression_hashes=(),
        )
    return ConsentDecision(
        allowed=True,
        scope=scope,
        basis=selected.basis,
        policy_id=policy.policy_id,
        reasons=("active consent matches policy",),
        consent_hashes=tuple(record.consent_hash for record in matching),
        suppression_hashes=(),
    )


def default_policies() -> tuple[CommunicationPolicy, ...]:
    professional_bases = frozenset(
        {
            ConsentBasis.EXPRESS,
            ConsentBasis.EXISTING_BUSINESS_RELATIONSHIP,
            ConsentBasis.EXISTING_NONBUSINESS_RELATIONSHIP,
            ConsentBasis.CONSPICUOUSLY_PUBLISHED_BUSINESS_CONTACT,
            ConsentBasis.INBOUND_REQUEST,
            ConsentBasis.REFERRAL,
            ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT,
        }
    )
    return (
        CommunicationPolicy(
            policy_id="POLICY-2026-0001",
            scope=ConsentScope.DIRECT_INDIVIDUAL_CONTACT,
            requires_express_consent=False,
            permitted_bases=professional_bases,
            maximum_messages_per_30_days=2,
            cooldown_days=14,
        ),
        CommunicationPolicy(
            policy_id="POLICY-2026-0002",
            scope=ConsentScope.RESEARCH_COLLABORATION,
            requires_express_consent=False,
            permitted_bases=professional_bases,
            maximum_messages_per_30_days=2,
            cooldown_days=14,
        ),
        CommunicationPolicy(
            policy_id="POLICY-2026-0003",
            scope=ConsentScope.SOFTWARE_PILOT,
            requires_express_consent=False,
            permitted_bases=professional_bases,
            maximum_messages_per_30_days=2,
            cooldown_days=14,
        ),
        CommunicationPolicy(
            policy_id="POLICY-2026-0004",
            scope=ConsentScope.COMMERCIAL_MARKETING,
            requires_express_consent=True,
            permitted_bases=frozenset({ConsentBasis.EXPRESS}),
            unsubscribe_required=True,
            maximum_messages_per_30_days=2,
            cooldown_days=14,
        ),
        CommunicationPolicy(
            policy_id="POLICY-2026-0005",
            scope=ConsentScope.REPLY_TO_REQUEST,
            requires_express_consent=False,
            permitted_bases=frozenset(
                {ConsentBasis.INBOUND_REQUEST, ConsentBasis.TRANSACTIONAL_NECESSITY}
            ),
            maximum_messages_per_30_days=12,
            cooldown_days=0,
        ),
    )


def audit_consent_records(
    records: Iterable[ConsentRecord],
    suppressions: Iterable[SuppressionEntry] = (),
) -> list[str]:
    materialized_records = tuple(records)
    materialized_suppressions = tuple(suppressions)
    errors: list[str] = []
    seen_consent_ids: set[str] = set()
    seen_suppression_ids: set[str] = set()
    for record in materialized_records:
        if record.consent_id in seen_consent_ids:
            errors.append(f"duplicate consent_id: {record.consent_id}")
        seen_consent_ids.add(record.consent_id)
    for entry in materialized_suppressions:
        if entry.suppression_id in seen_suppression_ids:
            errors.append(f"duplicate suppression_id: {entry.suppression_id}")
        seen_suppression_ids.add(entry.suppression_id)
    permanently_suppressed = {
        (entry.contact_id, scope)
        for entry in materialized_suppressions
        if entry.permanent
        for scope in entry.scopes
    }
    for record in materialized_records:
        if record.state is ConsentState.VALID:
            for scope in record.scopes:
                if (record.contact_id, scope) in permanently_suppressed:
                    errors.append(
                        f"valid consent conflicts with permanent suppression: {record.contact_id}/{scope.value}"
                    )
    return errors
