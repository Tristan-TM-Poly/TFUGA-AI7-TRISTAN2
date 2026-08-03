from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Iterable, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    assert_public_safe_text,
    canonical_hash,
    ensure_utc,
    is_sha256,
    normalize_domain,
    normalize_text,
    stable_unique,
    utc_now,
    validate_public_identifier,
)


class OrganizationType(str, Enum):
    UNIVERSITY = "university"
    RESEARCH_CENTER = "research_center"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    INCUBATOR = "incubator"
    ACCELERATOR = "accelerator"
    FINANCIAL_INSTITUTION = "financial_institution"
    CORPORATION = "corporation"
    SME = "sme"
    OPEN_SOURCE_PROJECT = "open_source_project"
    PROFESSIONAL_SERVICE = "professional_service"
    STANDARDS_BODY = "standards_body"
    UNKNOWN = "unknown"


class EvidenceKind(str, Enum):
    OFFICIAL_WEBSITE = "official_website"
    GOVERNMENT_REGISTER = "government_register"
    INSTITUTIONAL_DIRECTORY = "institutional_directory"
    PUBLICATION = "publication"
    GITHUB = "github"
    PUBLIC_ANNOUNCEMENT = "public_announcement"
    EXISTING_RELATIONSHIP = "existing_relationship"
    HUMAN_ATTESTATION = "human_attestation"


class RelationshipState(str, Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    MEETING = "meeting"
    PILOT = "pilot"
    PARTNER = "partner"
    CUSTOMER = "customer"
    CLOSED = "closed"
    SUPPRESSED = "suppressed"


_ORGANIZATION_SUFFIXES = (
    " incorporated",
    " inc.",
    " inc",
    " corporation",
    " corp.",
    " corp",
    " limited",
    " ltd.",
    " ltd",
    " société par actions",
    " s.a.",
    " llc",
)

_PUNCTUATION_RE = re.compile(r"[^a-z0-9à-ÿ]+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class OrganizationEvidence:
    evidence_id: str
    kind: EvidenceKind
    source_hash: str
    observed_at: datetime
    claim: str
    confidence: float
    official: bool = False
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            validate_public_identifier(self.evidence_id, prefix="EVID"),
        )
        if not is_sha256(self.source_hash):
            raise CanonicalizationError("organization evidence requires source_hash")
        claim = normalize_text(self.claim)
        assert_public_safe_text(claim, field="organization evidence claim", maximum=1000)
        if not claim:
            raise CanonicalizationError("organization evidence claim is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise CanonicalizationError("evidence confidence must be between 0 and 1")
        observed_at = ensure_utc(self.observed_at)
        expires_at = ensure_utc(self.expires_at) if self.expires_at else None
        if expires_at and expires_at <= observed_at:
            raise CanonicalizationError("evidence expiration must be after observation")
        object.__setattr__(self, "claim", claim)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "expires_at", expires_at)

    @property
    def evidence_hash(self) -> str:
        return canonical_hash(self)

    def active_at(self, moment: datetime | None = None) -> bool:
        current = ensure_utc(moment or utc_now())
        return self.expires_at is None or current <= self.expires_at


@dataclass(frozen=True, slots=True)
class OrganizationDivision:
    division_id: str
    name: str
    purpose: tuple[str, ...] = ()
    domain: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "division_id",
            validate_public_identifier(self.division_id, prefix="DIV"),
        )
        name = normalize_text(self.name)
        if not name:
            raise CanonicalizationError("division name is required")
        assert_public_safe_text(name, field="division name", maximum=240)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "purpose", stable_unique(self.purpose))
        if self.domain:
            object.__setattr__(self, "domain", normalize_domain(self.domain))


@dataclass(frozen=True, slots=True)
class Organization:
    organization_id: str
    canonical_name: str
    organization_type: OrganizationType
    country: str
    region: str | None = None
    domains: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    strategic_roles: tuple[str, ...] = ()
    evidence: tuple[OrganizationEvidence, ...] = ()
    divisions: tuple[OrganizationDivision, ...] = ()
    relationship_state: RelationshipState = RelationshipState.DISCOVERED
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "organization_id",
            validate_public_identifier(self.organization_id, prefix="ORG"),
        )
        canonical_name = normalize_text(self.canonical_name)
        assert_public_safe_text(canonical_name, field="organization name", maximum=240)
        if not canonical_name:
            raise CanonicalizationError("canonical organization name is required")
        country = normalize_text(self.country).upper()
        if len(country) not in {2, 3}:
            raise CanonicalizationError("country must use a 2 or 3 character code")
        region = normalize_text(self.region).upper() if self.region else None
        domains = tuple(sorted({normalize_domain(value) for value in self.domains}))
        aliases = stable_unique(self.aliases)
        if canonical_name in aliases:
            aliases = tuple(alias for alias in aliases if alias != canonical_name)
        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise CanonicalizationError("duplicate organization evidence IDs")
        division_ids = [item.division_id for item in self.divisions]
        if len(division_ids) != len(set(division_ids)):
            raise CanonicalizationError("duplicate organization division IDs")
        object.__setattr__(self, "canonical_name", canonical_name)
        object.__setattr__(self, "country", country)
        object.__setattr__(self, "region", region)
        object.__setattr__(self, "domains", domains)
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(self, "strategic_roles", stable_unique(self.strategic_roles))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "divisions", tuple(self.divisions))
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    @property
    def organization_hash(self) -> str:
        return canonical_hash(self)

    @property
    def canonical_key(self) -> str:
        primary_domain = self.domains[0] if self.domains else "no-domain"
        return f"{canonicalize_organization_name(self.canonical_name)}|{primary_domain}|{self.country}"

    def active_evidence(self, moment: datetime | None = None) -> tuple[OrganizationEvidence, ...]:
        return tuple(item for item in self.evidence if item.active_at(moment))

    def evidence_strength(self, moment: datetime | None = None) -> float:
        active = self.active_evidence(moment)
        if not active:
            return 0.0
        official_bonus = 0.15 if any(item.official for item in active) else 0.0
        independent_kinds = len({item.kind for item in active})
        diversity_bonus = min(0.20, max(0, independent_kinds - 1) * 0.05)
        weighted = sum(item.confidence * (1.20 if item.official else 1.0) for item in active)
        denominator = sum(1.20 if item.official else 1.0 for item in active)
        return min(1.0, weighted / denominator + official_bonus + diversity_bonus)

    def with_evidence(self, evidence: OrganizationEvidence) -> "Organization":
        if any(item.evidence_id == evidence.evidence_id for item in self.evidence):
            raise CanonicalizationError(f"duplicate evidence_id: {evidence.evidence_id}")
        return replace(self, evidence=tuple((*self.evidence, evidence)))

    def transition(self, target: RelationshipState) -> "Organization":
        allowed: Mapping[RelationshipState, frozenset[RelationshipState]] = {
            RelationshipState.DISCOVERED: frozenset(
                {RelationshipState.QUALIFIED, RelationshipState.CLOSED, RelationshipState.SUPPRESSED}
            ),
            RelationshipState.QUALIFIED: frozenset(
                {RelationshipState.CONTACTED, RelationshipState.CLOSED, RelationshipState.SUPPRESSED}
            ),
            RelationshipState.CONTACTED: frozenset(
                {RelationshipState.ENGAGED, RelationshipState.CLOSED, RelationshipState.SUPPRESSED}
            ),
            RelationshipState.ENGAGED: frozenset(
                {
                    RelationshipState.MEETING,
                    RelationshipState.PILOT,
                    RelationshipState.CLOSED,
                    RelationshipState.SUPPRESSED,
                }
            ),
            RelationshipState.MEETING: frozenset(
                {
                    RelationshipState.ENGAGED,
                    RelationshipState.PILOT,
                    RelationshipState.PARTNER,
                    RelationshipState.CUSTOMER,
                    RelationshipState.CLOSED,
                }
            ),
            RelationshipState.PILOT: frozenset(
                {
                    RelationshipState.PARTNER,
                    RelationshipState.CUSTOMER,
                    RelationshipState.CLOSED,
                }
            ),
            RelationshipState.PARTNER: frozenset(
                {RelationshipState.PILOT, RelationshipState.CUSTOMER, RelationshipState.CLOSED}
            ),
            RelationshipState.CUSTOMER: frozenset(
                {RelationshipState.PARTNER, RelationshipState.CLOSED}
            ),
            RelationshipState.CLOSED: frozenset(
                {RelationshipState.QUALIFIED, RelationshipState.SUPPRESSED}
            ),
            RelationshipState.SUPPRESSED: frozenset(),
        }
        if target not in allowed[self.relationship_state]:
            raise CanonicalizationError(
                f"organization transition {self.relationship_state.value} -> {target.value} is forbidden"
            )
        return replace(self, relationship_state=target)


def canonicalize_organization_name(value: str) -> str:
    normalized = normalize_text(value).casefold()
    changed = True
    while changed:
        changed = False
        for suffix in _ORGANIZATION_SUFFIXES:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip()
                changed = True
    normalized = _PUNCTUATION_RE.sub(" ", normalized)
    return " ".join(normalized.split())


def organization_similarity(left: Organization, right: Organization) -> float:
    score = 0.0
    if left.organization_id == right.organization_id:
        return 1.0
    left_name = canonicalize_organization_name(left.canonical_name)
    right_name = canonicalize_organization_name(right.canonical_name)
    if left_name == right_name:
        score += 0.50
    else:
        left_tokens = set(left_name.split())
        right_tokens = set(right_name.split())
        union = left_tokens | right_tokens
        if union:
            score += 0.40 * (len(left_tokens & right_tokens) / len(union))
    if set(left.domains) & set(right.domains):
        score += 0.40
    if left.country == right.country:
        score += 0.05
    if left.region and right.region and left.region == right.region:
        score += 0.05
    return min(1.0, score)


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    left_id: str
    right_id: str
    similarity: float
    reasons: tuple[str, ...]


def find_duplicate_candidates(
    organizations: Sequence[Organization], *, threshold: float = 0.75
) -> tuple[DuplicateCandidate, ...]:
    if not 0.0 <= threshold <= 1.0:
        raise CanonicalizationError("duplicate threshold must be between 0 and 1")
    candidates: list[DuplicateCandidate] = []
    for index, left in enumerate(organizations):
        for right in organizations[index + 1 :]:
            similarity = organization_similarity(left, right)
            if similarity < threshold:
                continue
            reasons: list[str] = []
            if canonicalize_organization_name(left.canonical_name) == canonicalize_organization_name(
                right.canonical_name
            ):
                reasons.append("canonical_name")
            if set(left.domains) & set(right.domains):
                reasons.append("domain")
            if left.country == right.country:
                reasons.append("country")
            candidates.append(
                DuplicateCandidate(
                    left_id=left.organization_id,
                    right_id=right.organization_id,
                    similarity=round(similarity, 6),
                    reasons=tuple(reasons),
                )
            )
    return tuple(sorted(candidates, key=lambda item: (-item.similarity, item.left_id, item.right_id)))


def merge_organizations(
    primary: Organization,
    duplicate: Organization,
    *,
    minimum_similarity: float = 0.75,
) -> Organization:
    similarity = organization_similarity(primary, duplicate)
    if similarity < minimum_similarity:
        raise CanonicalizationError(
            f"organization similarity {similarity:.3f} is below merge threshold"
        )
    evidence_by_id = {item.evidence_id: item for item in primary.evidence}
    for item in duplicate.evidence:
        evidence_by_id.setdefault(item.evidence_id, item)
    division_by_id = {item.division_id: item for item in primary.divisions}
    for item in duplicate.divisions:
        division_by_id.setdefault(item.division_id, item)
    metadata = dict(duplicate.metadata)
    metadata.update(primary.metadata)
    return Organization(
        organization_id=primary.organization_id,
        canonical_name=primary.canonical_name,
        organization_type=(
            primary.organization_type
            if primary.organization_type is not OrganizationType.UNKNOWN
            else duplicate.organization_type
        ),
        country=primary.country,
        region=primary.region or duplicate.region,
        domains=tuple((*primary.domains, *duplicate.domains)),
        aliases=tuple(
            (
                *primary.aliases,
                duplicate.canonical_name,
                *duplicate.aliases,
            )
        ),
        strategic_roles=tuple((*primary.strategic_roles, *duplicate.strategic_roles)),
        evidence=tuple(evidence_by_id.values()),
        divisions=tuple(division_by_id.values()),
        relationship_state=max(
            (primary.relationship_state, duplicate.relationship_state),
            key=lambda state: list(RelationshipState).index(state),
        ),
        metadata=metadata,
    )


def stale_evidence(
    organization: Organization,
    *,
    now: datetime | None = None,
    maximum_age_days: int = 365,
) -> tuple[OrganizationEvidence, ...]:
    if maximum_age_days < 1:
        raise CanonicalizationError("maximum evidence age must be positive")
    current = ensure_utc(now or utc_now())
    threshold = current - timedelta(days=maximum_age_days)
    return tuple(
        item
        for item in organization.evidence
        if item.observed_at < threshold or not item.active_at(current)
    )


def audit_organization(organization: Organization) -> list[str]:
    errors: list[str] = []
    if organization.relationship_state is not RelationshipState.DISCOVERED:
        if organization.evidence_strength() < 0.35:
            errors.append("non-discovered organization has insufficient evidence")
    if organization.organization_type is OrganizationType.UNKNOWN and organization.evidence:
        errors.append("organization type remains unknown despite available evidence")
    if any(division.domain and division.domain not in organization.domains for division in organization.divisions):
        errors.append("division domain is not registered on parent organization")
    if organization.relationship_state is RelationshipState.SUPPRESSED:
        if organization.metadata.get("suppression_reason") is None:
            errors.append("suppressed organization requires suppression_reason metadata")
    return errors


def audit_organizations(organizations: Iterable[Organization]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_keys: dict[str, str] = {}
    materialized = tuple(organizations)
    for organization in materialized:
        if organization.organization_id in seen_ids:
            errors.append(f"duplicate organization_id: {organization.organization_id}")
        seen_ids.add(organization.organization_id)
        if organization.canonical_key in seen_keys:
            errors.append(
                f"duplicate canonical organization key: {organization.organization_id} and "
                f"{seen_keys[organization.canonical_key]}"
            )
        else:
            seen_keys[organization.canonical_key] = organization.organization_id
        errors.extend(
            f"{organization.organization_id}: {error}"
            for error in audit_organization(organization)
        )
    for candidate in find_duplicate_candidates(materialized, threshold=0.90):
        errors.append(
            f"probable duplicate organizations: {candidate.left_id} / {candidate.right_id} "
            f"({candidate.similarity:.3f})"
        )
    return errors
