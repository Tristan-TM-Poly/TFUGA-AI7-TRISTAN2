from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from omega_company_outreach_t.foundation.canonical import (
    CanonicalizationError,
    canonical_hash,
    hmac_identifier,
    normalize_domain,
    normalize_email,
)
from omega_company_outreach_t.foundation.identity import (
    AuthorityGrant,
    AuthorityPermission,
    AuthorityRole,
    CompanyIdentity,
    DomainClaim,
    IdentityState,
    LegalEntityEvidence,
    require_distinct_approvers,
    resolve_authority,
)
from omega_company_outreach_t.foundation.organizations import (
    EvidenceKind,
    Organization,
    OrganizationDivision,
    OrganizationEvidence,
    OrganizationType,
    RelationshipState,
    audit_organizations,
    canonicalize_organization_name,
    find_duplicate_candidates,
    merge_organizations,
    organization_similarity,
    stale_evidence,
)

NOW = datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def evidence(identifier: str = "EVID-2026-0001", *, official: bool = True):
    return OrganizationEvidence(
        evidence_id=identifier,
        kind=EvidenceKind.OFFICIAL_WEBSITE,
        source_hash=HASH_A,
        observed_at=NOW,
        claim="The organization operates the verified public domain.",
        confidence=0.92,
        official=official,
    )


def organization(**overrides):
    payload = {
        "organization_id": "ORG-2026-0001",
        "canonical_name": "Example Research Institute",
        "organization_type": OrganizationType.RESEARCH_CENTER,
        "country": "CA",
        "region": "QC",
        "domains": ("example.org",),
        "aliases": ("Example Institute",),
        "strategic_roles": ("research_partner",),
        "evidence": (evidence(),),
        "relationship_state": RelationshipState.QUALIFIED,
    }
    payload.update(overrides)
    return Organization(**payload)


def grant(**overrides):
    payload = {
        "grant_id": "AUTH-2026-0001",
        "person_id": "tristan",
        "company_id": "tristan_parent_opco",
        "role": AuthorityRole.FOUNDER,
        "permissions": frozenset(
            {
                AuthorityPermission.PREPARE_OUTREACH,
                AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
            }
        ),
        "valid_from": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=30),
        "evidence_hash": HASH_A,
        "amount_limit_cad": 500,
        "jurisdictions": frozenset({"QC", "CA"}),
    }
    payload.update(overrides)
    return AuthorityGrant(**payload)


def test_normalization_and_hmac_are_deterministic():
    assert normalize_domain("Example.ORG.") == "example.org"
    assert normalize_email(" Name@Example.ORG ") == "name@example.org"
    first = hmac_identifier(b"x" * 32, "Name@Example.org", namespace="contact")
    second = hmac_identifier(b"x" * 32, " name@example.ORG ", namespace="CONTACT")
    assert first == second
    assert first.startswith("hmac-sha256:")


@pytest.mark.parametrize(
    "domain",
    ["localhost", "bad domain.ca", "-bad.example", "bad-.example", "example"],
)
def test_invalid_domains_are_rejected(domain):
    with pytest.raises(CanonicalizationError):
        normalize_domain(domain)


def test_internal_identity_uses_truthful_disclosure():
    identity = CompanyIdentity(
        company_id="tristan_research_foundry",
        display_name="Tristan Research Foundry",
        state=IdentityState.INTERNAL_ROLE,
        purpose=("research pilots", "universities"),
    )
    assert "non présenté comme entité constituée" in identity.disclosure_line()
    assert not identity.can_claim_corporate_sender()
    assert identity.identity_hash == canonical_hash(identity)


def test_domain_verified_state_requires_verified_claim():
    with pytest.raises(CanonicalizationError, match="verified domain"):
        CompanyIdentity(
            company_id="tristan_software_labs",
            display_name="Tristan Software Labs",
            state=IdentityState.DOMAIN_VERIFIED,
            purpose=("software pilots",),
            domains=(DomainClaim("example.org"),),
        )


def test_verified_domain_requires_complete_evidence():
    with pytest.raises(CanonicalizationError, match="verification method"):
        DomainClaim(domain="example.org", verified=True)
    claim = DomainClaim(
        domain="example.org",
        verified=True,
        verification_method="dns_txt",
        evidence_hash=HASH_A,
        verified_at=NOW,
    )
    assert claim.verified
    assert claim.domain == "example.org"


def test_identity_cannot_skip_states():
    identity = CompanyIdentity(
        company_id="tristan_parent_opco",
        display_name="Tristan Parent OpCo",
        state=IdentityState.INTERNAL_ROLE,
        purpose=("strategy",),
    )
    with pytest.raises(CanonicalizationError, match="not allowed"):
        identity.transition(IdentityState.LEGAL_ENTITY_VERIFIED)


def test_contract_ready_requires_legal_entity_and_domain_path():
    claim = DomainClaim(
        domain="example.org",
        verified=True,
        verification_method="dns_txt",
        evidence_hash=HASH_A,
        verified_at=NOW,
    )
    legal = LegalEntityEvidence(
        jurisdiction="QC",
        legal_name="Example Québec inc.",
        registration_hash=HASH_B,
        verified_at=NOW,
        verifier_role=AuthorityRole.LEGAL_REVIEWER,
    )
    identity = CompanyIdentity(
        company_id="tristan_parent_opco",
        display_name="Tristan Parent OpCo",
        state=IdentityState.BRAND_CANDIDATE,
        purpose=("strategy",),
        domains=(claim,),
    )
    identity = identity.transition(IdentityState.DOMAIN_VERIFIED)
    identity = identity.transition(IdentityState.LEGAL_ENTITY_VERIFIED, legal_entity=legal)
    identity = identity.transition(IdentityState.BANKING_VERIFIED)
    identity = identity.transition(IdentityState.TAX_VERIFIED)
    identity = identity.transition(
        IdentityState.CONTRACT_READY, external_commitment_allowed=True
    )
    assert identity.external_commitment_allowed
    assert identity.is_legal_entity_verified
    assert identity.can_claim_corporate_sender()


def test_authority_is_company_permission_amount_and_jurisdiction_bound():
    authority = grant()
    assert authority.authorizes(
        AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
        company_id="tristan_parent_opco",
        moment=NOW,
        amount_cad=100,
        jurisdiction="QC",
    )
    assert not authority.authorizes(
        AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
        company_id="tristan_research_foundry",
        moment=NOW,
    )
    assert not authority.authorizes(
        AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
        company_id="tristan_parent_opco",
        moment=NOW,
        amount_cad=501,
    )
    assert not authority.authorizes(
        AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
        company_id="tristan_parent_opco",
        moment=NOW,
        jurisdiction="US",
    )


def test_expired_and_revoked_authority_are_inactive():
    expired = grant(valid_from=NOW - timedelta(days=10), valid_until=NOW - timedelta(days=1))
    assert not expired.active_at(NOW)
    revoked = grant().revoke(at=NOW)
    assert not revoked.active_at(NOW + timedelta(seconds=1))


def test_resolve_authority_returns_only_matching_grants():
    other = grant(
        grant_id="AUTH-2026-0002",
        person_id="reviewer",
        role=AuthorityRole.LEGAL_REVIEWER,
        permissions=frozenset({AuthorityPermission.APPROVE_CONTRACT}),
        amount_limit_cad=None,
    )
    matches = resolve_authority(
        (grant(), other),
        AuthorityPermission.APPROVE_LOW_RISK_OUTREACH,
        company_id="tristan_parent_opco",
        moment=NOW,
    )
    assert [item.grant_id for item in matches] == ["AUTH-2026-0001"]


def test_distinct_approvers_cannot_be_same_person_with_different_case():
    first = grant(person_id="Tristan")
    second = grant(grant_id="AUTH-2026-0002", person_id="tristan")
    with pytest.raises(CanonicalizationError, match="distinct"):
        require_distinct_approvers((first, second), 2)


def test_organization_name_canonicalization_removes_legal_suffixes():
    assert canonicalize_organization_name("Example Research Inc.") == "example research"
    assert canonicalize_organization_name("Example—Research Corporation") == "example research"


def test_organization_evidence_strength_rewards_official_diversity():
    official = evidence()
    publication = OrganizationEvidence(
        evidence_id="EVID-2026-0002",
        kind=EvidenceKind.PUBLICATION,
        source_hash=HASH_B,
        observed_at=NOW,
        claim="Independent publication confirms the research program.",
        confidence=0.80,
        official=False,
    )
    item = organization(evidence=(official, publication))
    assert item.evidence_strength(NOW) > 0.90


def test_organization_requires_evidence_after_discovery():
    weak = organization(evidence=(), relationship_state=RelationshipState.QUALIFIED)
    errors = audit_organizations((weak,))
    assert any("insufficient evidence" in error for error in errors)


def test_duplicate_detection_uses_name_domain_and_geography():
    first = organization()
    second = organization(
        organization_id="ORG-2026-0002",
        canonical_name="Example Research Institute Inc.",
        aliases=(),
    )
    candidates = find_duplicate_candidates((first, second), threshold=0.75)
    assert len(candidates) == 1
    assert candidates[0].similarity >= 0.9
    assert {"canonical_name", "domain", "country"}.issubset(candidates[0].reasons)


def test_organization_similarity_is_low_for_unrelated_entities():
    first = organization()
    second = organization(
        organization_id="ORG-2026-0002",
        canonical_name="Different Accelerator",
        organization_type=OrganizationType.ACCELERATOR,
        domains=("different.ca",),
        evidence=(
            OrganizationEvidence(
                evidence_id="EVID-2026-0002",
                kind=EvidenceKind.OFFICIAL_WEBSITE,
                source_hash=HASH_B,
                observed_at=NOW,
                claim="Official accelerator website.",
                confidence=0.9,
                official=True,
            ),
        ),
    )
    assert organization_similarity(first, second) < 0.3


def test_merge_organizations_preserves_primary_identity_and_union_evidence():
    first = organization()
    second = organization(
        organization_id="ORG-2026-0002",
        canonical_name="Example Research Institute Inc.",
        aliases=("ERI",),
        evidence=(
            OrganizationEvidence(
                evidence_id="EVID-2026-0002",
                kind=EvidenceKind.PUBLICATION,
                source_hash=HASH_B,
                observed_at=NOW,
                claim="Independent publication.",
                confidence=0.8,
            ),
        ),
        divisions=(
            OrganizationDivision(
                division_id="DIV-2026-0001",
                name="AI Laboratory",
                purpose=("artificial intelligence",),
                domain="example.org",
            ),
        ),
    )
    merged = merge_organizations(first, second)
    assert merged.organization_id == first.organization_id
    assert {item.evidence_id for item in merged.evidence} == {
        "EVID-2026-0001",
        "EVID-2026-0002",
    }
    assert "ERI" in merged.aliases
    assert merged.divisions[0].name == "AI Laboratory"


def test_stale_evidence_detects_age_and_expiration():
    old = OrganizationEvidence(
        evidence_id="EVID-2026-0003",
        kind=EvidenceKind.PUBLIC_ANNOUNCEMENT,
        source_hash=HASH_C,
        observed_at=NOW - timedelta(days=800),
        claim="Old announcement.",
        confidence=0.7,
        expires_at=NOW - timedelta(days=1),
    )
    item = organization(evidence=(old,), relationship_state=RelationshipState.DISCOVERED)
    assert stale_evidence(item, now=NOW, maximum_age_days=365) == (old,)


@pytest.mark.parametrize(
    "current,target",
    [
        (RelationshipState.DISCOVERED, RelationshipState.QUALIFIED),
        (RelationshipState.QUALIFIED, RelationshipState.CONTACTED),
        (RelationshipState.CONTACTED, RelationshipState.ENGAGED),
        (RelationshipState.ENGAGED, RelationshipState.MEETING),
        (RelationshipState.MEETING, RelationshipState.PILOT),
        (RelationshipState.PILOT, RelationshipState.PARTNER),
    ],
)
def test_valid_organization_transitions(current, target):
    item = organization(relationship_state=current)
    assert item.transition(target).relationship_state is target


def test_suppressed_organization_is_terminal():
    item = organization(
        relationship_state=RelationshipState.SUPPRESSED,
        metadata={"suppression_reason": "explicit request"},
    )
    with pytest.raises(CanonicalizationError):
        item.transition(RelationshipState.QUALIFIED)
