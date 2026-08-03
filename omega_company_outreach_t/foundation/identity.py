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
    normalize_domain,
    normalize_text,
    stable_unique,
    utc_now,
    validate_public_identifier,
)


class IdentityState(str, Enum):
    CONCEPT = "concept"
    INTERNAL_ROLE = "internal_role"
    BRAND_CANDIDATE = "brand_candidate"
    DOMAIN_VERIFIED = "domain_verified"
    LEGAL_ENTITY_VERIFIED = "legal_entity_verified"
    BANKING_VERIFIED = "banking_verified"
    TAX_VERIFIED = "tax_verified"
    CONTRACT_READY = "contract_ready"
    PRODUCTION_COMPANY = "production_company"


class AuthorityPermission(str, Enum):
    PREPARE_OUTREACH = "prepare_outreach"
    APPROVE_LOW_RISK_OUTREACH = "approve_low_risk_outreach"
    APPROVE_PARTNERSHIP_REQUEST = "approve_partnership_request"
    APPROVE_PRICING_DISCUSSION = "approve_pricing_discussion"
    APPROVE_PROPOSAL = "approve_proposal"
    APPROVE_CONTRACT = "approve_contract"
    APPROVE_PAYMENT = "approve_payment"
    APPROVE_GOVERNMENT_FILING = "approve_government_filing"
    APPROVE_PRODUCTION_ACTIVATION = "approve_production_activation"


class AuthorityRole(str, Enum):
    FOUNDER = "founder"
    DIRECTOR = "director"
    OFFICER = "officer"
    OUTREACH_OPERATOR = "outreach_operator"
    TECHNICAL_APPROVER = "technical_approver"
    FINANCE_APPROVER = "finance_approver"
    PRIVACY_OFFICER = "privacy_officer"
    LEGAL_REVIEWER = "legal_reviewer"
    EXTERNAL_PROFESSIONAL = "external_professional"


_STATE_ORDER = tuple(IdentityState)
_STATE_INDEX = {state: index for index, state in enumerate(_STATE_ORDER)}

_ALLOWED_TRANSITIONS: Mapping[IdentityState, frozenset[IdentityState]] = {
    IdentityState.CONCEPT: frozenset({IdentityState.INTERNAL_ROLE}),
    IdentityState.INTERNAL_ROLE: frozenset({IdentityState.BRAND_CANDIDATE}),
    IdentityState.BRAND_CANDIDATE: frozenset(
        {IdentityState.DOMAIN_VERIFIED, IdentityState.INTERNAL_ROLE}
    ),
    IdentityState.DOMAIN_VERIFIED: frozenset(
        {IdentityState.LEGAL_ENTITY_VERIFIED, IdentityState.BRAND_CANDIDATE}
    ),
    IdentityState.LEGAL_ENTITY_VERIFIED: frozenset(
        {IdentityState.BANKING_VERIFIED, IdentityState.DOMAIN_VERIFIED}
    ),
    IdentityState.BANKING_VERIFIED: frozenset(
        {IdentityState.TAX_VERIFIED, IdentityState.LEGAL_ENTITY_VERIFIED}
    ),
    IdentityState.TAX_VERIFIED: frozenset(
        {IdentityState.CONTRACT_READY, IdentityState.BANKING_VERIFIED}
    ),
    IdentityState.CONTRACT_READY: frozenset(
        {IdentityState.PRODUCTION_COMPANY, IdentityState.TAX_VERIFIED}
    ),
    IdentityState.PRODUCTION_COMPANY: frozenset({IdentityState.CONTRACT_READY}),
}


@dataclass(frozen=True, slots=True)
class DomainClaim:
    domain: str
    verified: bool = False
    verification_method: str | None = None
    evidence_hash: str | None = None
    verified_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", normalize_domain(self.domain))
        if self.verified:
            if not self.verification_method:
                raise CanonicalizationError("verified domain requires a verification method")
            if not is_sha256(self.evidence_hash):
                raise CanonicalizationError("verified domain requires a canonical evidence hash")
            if self.verified_at is None:
                raise CanonicalizationError("verified domain requires verified_at")
            object.__setattr__(self, "verified_at", ensure_utc(self.verified_at))
        elif any((self.verification_method, self.evidence_hash, self.verified_at)):
            raise CanonicalizationError("unverified domain cannot contain verification evidence")


@dataclass(frozen=True, slots=True)
class LegalEntityEvidence:
    jurisdiction: str
    legal_name: str
    registration_hash: str
    verified_at: datetime
    verifier_role: AuthorityRole

    def __post_init__(self) -> None:
        jurisdiction = normalize_text(self.jurisdiction).upper()
        legal_name = normalize_text(self.legal_name)
        if not jurisdiction or len(jurisdiction) > 24:
            raise CanonicalizationError("invalid legal jurisdiction")
        if not legal_name or len(legal_name) > 240:
            raise CanonicalizationError("invalid legal name")
        if not is_sha256(self.registration_hash):
            raise CanonicalizationError("registration_hash must be canonical SHA-256")
        object.__setattr__(self, "jurisdiction", jurisdiction)
        object.__setattr__(self, "legal_name", legal_name)
        object.__setattr__(self, "verified_at", ensure_utc(self.verified_at))


@dataclass(frozen=True, slots=True)
class CompanyIdentity:
    company_id: str
    display_name: str
    state: IdentityState
    purpose: tuple[str, ...]
    domains: tuple[DomainClaim, ...] = ()
    legal_entity: LegalEntityEvidence | None = None
    authenticated_sender_type: str = "personal_gmail"
    external_commitment_allowed: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        company_id = normalize_text(self.company_id).casefold().replace(" ", "_")
        if not company_id.startswith("tristan_"):
            raise CanonicalizationError("company_id must use the tristan_ namespace")
        display_name = normalize_text(self.display_name)
        if not display_name:
            raise CanonicalizationError("display_name is required")
        purpose = stable_unique(self.purpose)
        if not purpose:
            raise CanonicalizationError("at least one company purpose is required")
        domain_names = [claim.domain for claim in self.domains]
        if len(domain_names) != len(set(domain_names)):
            raise CanonicalizationError("duplicate domain claims")
        if self.state is IdentityState.DOMAIN_VERIFIED and not self.has_verified_domain:
            raise CanonicalizationError("DOMAIN_VERIFIED requires a verified domain")
        if _STATE_INDEX[self.state] >= _STATE_INDEX[IdentityState.LEGAL_ENTITY_VERIFIED]:
            if self.legal_entity is None:
                raise CanonicalizationError("legal identity states require legal entity evidence")
        if self.external_commitment_allowed and _STATE_INDEX[self.state] < _STATE_INDEX[
            IdentityState.CONTRACT_READY
        ]:
            raise CanonicalizationError(
                "external commitments require at least CONTRACT_READY identity state"
            )
        object.__setattr__(self, "company_id", company_id)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "purpose", purpose)
        object.__setattr__(self, "domains", tuple(self.domains))
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    @property
    def has_verified_domain(self) -> bool:
        return any(claim.verified for claim in self.domains)

    @property
    def is_legal_entity_verified(self) -> bool:
        return self.legal_entity is not None and _STATE_INDEX[self.state] >= _STATE_INDEX[
            IdentityState.LEGAL_ENTITY_VERIFIED
        ]

    @property
    def identity_hash(self) -> str:
        return canonical_hash(self)

    def disclosure_line(self) -> str:
        if self.state is IdentityState.PRODUCTION_COMPANY and self.is_legal_entity_verified:
            return self.legal_entity.legal_name if self.legal_entity else self.display_name
        if self.is_legal_entity_verified:
            return f"{self.display_name} — identité légale vérifiée, rôle opérationnel déclaré"
        return (
            f"{self.display_name} — rôle opérationnel interne/candidat, "
            "non présenté comme entité constituée"
        )

    def can_claim_corporate_sender(self) -> bool:
        return self.is_legal_entity_verified and self.has_verified_domain

    def transition(
        self,
        target: IdentityState,
        *,
        legal_entity: LegalEntityEvidence | None = None,
        external_commitment_allowed: bool | None = None,
    ) -> "CompanyIdentity":
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise CanonicalizationError(
                f"identity transition {self.state.value} -> {target.value} is not allowed"
            )
        candidate = replace(
            self,
            state=target,
            legal_entity=legal_entity if legal_entity is not None else self.legal_entity,
            external_commitment_allowed=(
                self.external_commitment_allowed
                if external_commitment_allowed is None
                else external_commitment_allowed
            ),
        )
        return candidate


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    grant_id: str
    person_id: str
    company_id: str
    role: AuthorityRole
    permissions: frozenset[AuthorityPermission]
    valid_from: datetime
    valid_until: datetime
    evidence_hash: str
    amount_limit_cad: int | None = None
    jurisdictions: frozenset[str] = frozenset()
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "grant_id", validate_public_identifier(self.grant_id, prefix="AUTH")
        )
        person_id = normalize_text(self.person_id).casefold()
        company_id = normalize_text(self.company_id).casefold().replace(" ", "_")
        if not person_id:
            raise CanonicalizationError("person_id is required")
        if not company_id.startswith("tristan_"):
            raise CanonicalizationError("authority company_id must use tristan_ namespace")
        if not self.permissions:
            raise CanonicalizationError("authority grant requires permissions")
        valid_from = ensure_utc(self.valid_from)
        valid_until = ensure_utc(self.valid_until)
        if valid_until <= valid_from:
            raise CanonicalizationError("authority valid_until must be after valid_from")
        if not is_sha256(self.evidence_hash):
            raise CanonicalizationError("authority evidence_hash must be canonical SHA-256")
        if self.amount_limit_cad is not None and self.amount_limit_cad < 0:
            raise CanonicalizationError("amount_limit_cad cannot be negative")
        jurisdictions = frozenset(
            normalize_text(value).upper() for value in self.jurisdictions if value.strip()
        )
        revoked_at = ensure_utc(self.revoked_at) if self.revoked_at else None
        object.__setattr__(self, "person_id", person_id)
        object.__setattr__(self, "company_id", company_id)
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)
        object.__setattr__(self, "jurisdictions", jurisdictions)
        object.__setattr__(self, "revoked_at", revoked_at)

    @property
    def grant_hash(self) -> str:
        return canonical_hash(self)

    def active_at(self, moment: datetime | None = None) -> bool:
        current = ensure_utc(moment or utc_now())
        return (
            self.valid_from <= current <= self.valid_until
            and (self.revoked_at is None or current < self.revoked_at)
        )

    def authorizes(
        self,
        permission: AuthorityPermission,
        *,
        company_id: str,
        moment: datetime | None = None,
        amount_cad: int | None = None,
        jurisdiction: str | None = None,
    ) -> bool:
        if not self.active_at(moment):
            return False
        if normalize_text(company_id).casefold().replace(" ", "_") != self.company_id:
            return False
        if permission not in self.permissions:
            return False
        if amount_cad is not None:
            if amount_cad < 0:
                return False
            if self.amount_limit_cad is None or amount_cad > self.amount_limit_cad:
                return False
        if jurisdiction is not None and self.jurisdictions:
            if normalize_text(jurisdiction).upper() not in self.jurisdictions:
                return False
        return True

    def revoke(self, *, at: datetime | None = None) -> "AuthorityGrant":
        current = ensure_utc(at or utc_now())
        if current < self.valid_from:
            raise CanonicalizationError("grant cannot be revoked before it begins")
        return replace(self, revoked_at=current)


def resolve_authority(
    grants: Iterable[AuthorityGrant],
    permission: AuthorityPermission,
    *,
    company_id: str,
    moment: datetime | None = None,
    amount_cad: int | None = None,
    jurisdiction: str | None = None,
) -> tuple[AuthorityGrant, ...]:
    matches = [
        grant
        for grant in grants
        if grant.authorizes(
            permission,
            company_id=company_id,
            moment=moment,
            amount_cad=amount_cad,
            jurisdiction=jurisdiction,
        )
    ]
    return tuple(sorted(matches, key=lambda grant: (grant.role.value, grant.grant_id)))


def require_distinct_approvers(grants: Iterable[AuthorityGrant], count: int) -> None:
    if count < 1:
        raise CanonicalizationError("required approver count must be positive")
    people = {grant.person_id.casefold() for grant in grants}
    if len(people) < count:
        raise CanonicalizationError(f"at least {count} distinct approvers are required")
