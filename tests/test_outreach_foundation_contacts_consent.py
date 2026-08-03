from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from omega_company_outreach_t.foundation.canonical import CanonicalizationError
from omega_company_outreach_t.foundation.contacts import (
    ContactEvidence,
    ContactPreferences,
    ContactRecord,
    ContactSource,
    ContactState,
    RoleCategory,
    audit_contacts,
    contact_similarity,
    find_contact_duplicates,
)
from omega_company_outreach_t.foundation.consent import (
    CommunicationPolicy,
    ConsentBasis,
    ConsentRecord,
    ConsentScope,
    ConsentState,
    SuppressionEntry,
    SuppressionReason,
    audit_consent_records,
    default_policies,
    resolve_consent,
)

NOW = datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
RECIPIENT_A = "hmac-sha256:" + "1" * 64
RECIPIENT_B = "hmac-sha256:" + "2" * 64


def contact_evidence(**overrides):
    payload = {
        "evidence_id": "EVID-2026-1001",
        "source": ContactSource.OFFICIAL_WEBSITE,
        "source_hash": HASH_A,
        "observed_at": NOW,
        "organization_domain": "example.org",
        "role_verified": True,
        "relationship_verified": False,
        "confidence": 0.85,
    }
    payload.update(overrides)
    return ContactEvidence(**payload)


def contact(**overrides):
    payload = {
        "contact_id": "CNT-2026-0001",
        "organization_id": "ORG-2026-0001",
        "role_category": RoleCategory.PROGRAM_MANAGER,
        "state": ContactState.CONTACTABLE,
        "recipient_hash": RECIPIENT_A,
        "private_email_ref": "vault://contacts/CNT-2026-0001/email",
        "private_name_ref": "vault://contacts/CNT-2026-0001/name",
        "title": "Program Manager",
        "department": "Innovation",
        "domain": "example.org",
        "sources": (contact_evidence(),),
        "preferences": ContactPreferences(),
        "tags": ("program", "quebec"),
        "created_at": NOW,
        "updated_at": NOW,
    }
    payload.update(overrides)
    return ContactRecord(**payload)


def consent(**overrides):
    payload = {
        "consent_id": "CONSENT-2026-0001",
        "contact_id": "CNT-2026-0001",
        "basis": ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT,
        "scopes": frozenset(
            {ConsentScope.DIRECT_INDIVIDUAL_CONTACT, ConsentScope.SOFTWARE_PILOT}
        ),
        "state": ConsentState.VALID,
        "obtained_at": NOW,
        "evidence_hash": HASH_B,
    }
    payload.update(overrides)
    return ConsentRecord(**payload)


def suppression(**overrides):
    payload = {
        "suppression_id": "SUPPRESS-2026-0001",
        "contact_id": "CNT-2026-0001",
        "reason": SuppressionReason.UNSUBSCRIBE,
        "created_at": NOW,
        "evidence_hash": HASH_C,
        "permanent": True,
        "scopes": frozenset(ConsentScope),
    }
    payload.update(overrides)
    return SuppressionEntry(**payload)


def policy(scope=ConsentScope.SOFTWARE_PILOT, **overrides):
    payload = {
        "policy_id": "POLICY-2026-1001",
        "scope": scope,
        "requires_express_consent": False,
        "permitted_bases": frozenset(
            {
                ConsentBasis.EXPRESS,
                ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT,
                ConsentBasis.EXISTING_BUSINESS_RELATIONSHIP,
            }
        ),
        "identification_required": True,
        "unsubscribe_required": False,
        "maximum_messages_per_30_days": 2,
        "cooldown_days": 14,
        "human_approval_required": True,
    }
    payload.update(overrides)
    return CommunicationPolicy(**payload)


def test_contact_contains_only_private_references_not_raw_addresses():
    item = contact()
    assert item.private_email_ref.startswith("vault://")
    assert "@" not in item.private_email_ref
    assert item.recipient_hash.startswith("hmac-sha256:")
    assert item.can_be_contacted()


@pytest.mark.parametrize(
    "reference",
    ["person@example.org", "/private/contact", "vault://bad/../secret", "vault://bad path"],
)
def test_invalid_private_references_are_rejected(reference):
    with pytest.raises(CanonicalizationError):
        contact(private_email_ref=reference)


def test_contactable_contact_requires_evidence():
    with pytest.raises(CanonicalizationError, match="require evidence"):
        contact(sources=())


def test_professional_verification_uses_role_and_confidence():
    assert contact().professionally_verified
    weak = contact(
        state=ContactState.VERIFIED,
        sources=(contact_evidence(role_verified=False, confidence=0.4),),
    )
    assert not weak.professionally_verified


def test_contact_transition_to_suppressed_updates_preferences():
    suppressed = contact().transition(ContactState.SUPPRESSED, now=NOW + timedelta(hours=1))
    assert suppressed.state is ContactState.SUPPRESSED
    assert suppressed.preferences.no_follow_up
    assert suppressed.preferences.preferred_channel == "none"
    assert not suppressed.can_be_contacted()


def test_suppressed_contact_is_terminal():
    item = contact().transition(ContactState.SUPPRESSED)
    with pytest.raises(CanonicalizationError):
        item.transition(ContactState.VERIFIED)


def test_bounced_contact_cannot_be_contacted():
    bounced = contact(state=ContactState.BOUNCED)
    assert not bounced.can_be_contacted()


def test_contact_duplicate_detection_prioritizes_recipient_hash():
    first = contact()
    second = contact(
        contact_id="CNT-2026-0002",
        private_email_ref="vault://contacts/CNT-2026-0002/email",
        private_name_ref=None,
    )
    similarity = contact_similarity(first, second)
    assert similarity.confidence >= 0.9
    assert "recipient_hash" in similarity.reasons
    duplicates = find_contact_duplicates((first, second))
    assert duplicates == (similarity,)


def test_different_recipient_hashes_do_not_trigger_strong_duplicate():
    first = contact()
    second = contact(
        contact_id="CNT-2026-0002",
        recipient_hash=RECIPIENT_B,
        private_email_ref="vault://contacts/CNT-2026-0002/email",
        private_name_ref=None,
        role_category=RoleCategory.ENGINEER,
    )
    assert contact_similarity(first, second).confidence < 0.75


def test_audit_contacts_detects_duplicate_recipient():
    first = contact()
    second = contact(
        contact_id="CNT-2026-0002",
        private_email_ref="vault://contacts/CNT-2026-0002/email",
        private_name_ref=None,
    )
    errors = audit_contacts((first, second))
    assert any("duplicate recipient hash" in error for error in errors)


def test_contact_preferences_enforce_message_limit():
    with pytest.raises(CanonicalizationError):
        ContactPreferences(maximum_messages_per_30_days=21)
    preferences = ContactPreferences(
        language="en-ca",
        preferred_channel="portal",
        maximum_messages_per_30_days=0,
    )
    assert preferences.language == "en-ca"
    assert preferences.maximum_messages_per_30_days == 0


def test_consent_allows_matching_scope_and_policy():
    decision = resolve_consent(
        "CNT-2026-0001",
        ConsentScope.SOFTWARE_PILOT,
        policy(),
        records=(consent(),),
        moment=NOW + timedelta(days=1),
    )
    assert decision.allowed
    assert decision.basis is ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT
    assert decision.consent_hashes == (consent().consent_hash,)


def test_missing_scope_is_denied():
    decision = resolve_consent(
        "CNT-2026-0001",
        ConsentScope.RESEARCH_COLLABORATION,
        policy(scope=ConsentScope.RESEARCH_COLLABORATION),
        records=(consent(),),
        moment=NOW,
    )
    assert not decision.allowed
    assert "no active consent" in decision.reasons[0]


def test_expired_consent_is_denied_without_mutating_record():
    record = consent(expires_at=NOW + timedelta(days=1))
    assert record.effective_state(NOW + timedelta(days=2)) is ConsentState.EXPIRED
    decision = resolve_consent(
        record.contact_id,
        ConsentScope.SOFTWARE_PILOT,
        policy(),
        records=(record,),
        moment=NOW + timedelta(days=2),
    )
    assert not decision.allowed
    assert record.state is ConsentState.VALID


def test_withdrawal_is_irreversible_record_state():
    withdrawn = consent().withdraw(at=NOW + timedelta(hours=1))
    assert withdrawn.state is ConsentState.WITHDRAWN
    assert withdrawn.withdrawn_at == NOW + timedelta(hours=1)
    assert not withdrawn.allows(ConsentScope.SOFTWARE_PILOT, NOW + timedelta(hours=2))


def test_suppression_overrides_valid_consent():
    decision = resolve_consent(
        "CNT-2026-0001",
        ConsentScope.SOFTWARE_PILOT,
        policy(),
        records=(consent(),),
        suppressions=(suppression(),),
        moment=NOW + timedelta(days=1),
    )
    assert not decision.allowed
    assert decision.reasons == ("active suppression",)
    assert decision.suppression_hashes == (suppression().suppression_hash,)


def test_temporary_suppression_expires():
    temporary = suppression(
        suppression_id="SUPPRESS-2026-0002",
        permanent=False,
        expires_at=NOW + timedelta(days=3),
    )
    assert temporary.blocks(ConsentScope.SOFTWARE_PILOT, NOW + timedelta(days=2))
    assert not temporary.blocks(ConsentScope.SOFTWARE_PILOT, NOW + timedelta(days=4))


def test_permanent_suppression_cannot_have_expiration():
    with pytest.raises(CanonicalizationError):
        suppression(expires_at=NOW + timedelta(days=3))


def test_express_marketing_policy_accepts_only_express_basis():
    marketing_policy = CommunicationPolicy(
        policy_id="POLICY-2026-1002",
        scope=ConsentScope.COMMERCIAL_MARKETING,
        requires_express_consent=True,
        permitted_bases=frozenset({ConsentBasis.EXPRESS}),
        unsubscribe_required=True,
    )
    professional = consent(
        scopes=frozenset({ConsentScope.COMMERCIAL_MARKETING}),
        basis=ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT,
    )
    decision = resolve_consent(
        professional.contact_id,
        ConsentScope.COMMERCIAL_MARKETING,
        marketing_policy,
        records=(professional,),
        moment=NOW,
    )
    assert not decision.allowed
    expressed = consent(
        scopes=frozenset({ConsentScope.COMMERCIAL_MARKETING}),
        basis=ConsentBasis.EXPRESS,
    )
    assert resolve_consent(
        expressed.contact_id,
        ConsentScope.COMMERCIAL_MARKETING,
        marketing_policy,
        records=(expressed,),
        moment=NOW,
    ).allowed


def test_invalid_express_policy_cannot_permit_other_bases():
    with pytest.raises(CanonicalizationError, match="EXPRESS"):
        CommunicationPolicy(
            policy_id="POLICY-2026-1003",
            scope=ConsentScope.COMMERCIAL_MARKETING,
            requires_express_consent=True,
            permitted_bases=frozenset(
                {ConsentBasis.EXPRESS, ConsentBasis.EXISTING_BUSINESS_RELATIONSHIP}
            ),
        )


def test_audit_detects_valid_consent_conflicting_with_permanent_suppression():
    errors = audit_consent_records((consent(),), (suppression(),))
    assert any("conflicts with permanent suppression" in error for error in errors)


def test_default_policy_catalog_has_unique_scope_policy_pairs():
    policies = default_policies()
    assert len(policies) >= 5
    assert len({item.policy_id for item in policies}) == len(policies)
    assert any(item.scope is ConsentScope.COMMERCIAL_MARKETING for item in policies)
    marketing = next(item for item in policies if item.scope is ConsentScope.COMMERCIAL_MARKETING)
    assert marketing.requires_express_consent
    assert marketing.unsubscribe_required


@pytest.mark.parametrize(
    "state",
    [ConsentState.WITHDRAWN, ConsentState.DENIED, ConsentState.SUPPRESSED, ConsentState.EXPIRED],
)
def test_nonvalid_consent_states_never_allow(state):
    kwargs = {}
    if state in {ConsentState.WITHDRAWN, ConsentState.SUPPRESSED}:
        kwargs["withdrawn_at"] = NOW + timedelta(minutes=1)
    record = consent(state=state, **kwargs)
    assert not record.allows(ConsentScope.SOFTWARE_PILOT, NOW + timedelta(hours=1))
