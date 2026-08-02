from datetime import datetime, timezone

import pytest

from omega_mail_t.officialization import (
    ApprovalRecord,
    CompanyIdentity,
    CompanyState,
    ComplianceContext,
    MailAuthority,
    MessageClass,
    OfficialDecision,
    OfficialMessageDraft,
    OfficializationGate,
)
from omega_mail_t.production import DryRunProvider, SMTPConfig, SMTPProvider, deliver_one


def draft(subject: str = "Avis administratif") -> OfficialMessageDraft:
    return OfficialMessageDraft(
        sender="corporate@tristan.example",
        recipients=("known.partner@example.net",),
        subject=subject,
        body="Message administratif vérifié.",
        metadata={"purpose": "officialization-test"},
    )


def company(**changes) -> CompanyIdentity:
    data = dict(
        company_id="tristan_parent_opco",
        conceptual_name="Tristan Company Foundry",
        state=CompanyState.PRODUCTION_AUTHORIZED,
        legal_name="Tristan Example Inc.",
        jurisdiction="QC",
        neq="1234567890",
        domain="tristan.example",
        legal_identity_verified=True,
        domain_control_verified=True,
        spf_verified=True,
        dkim_verified=True,
        dmarc_verified=True,
        external_send_enabled=True,
        evidence_ids=("certificate:demo", "dns:audit"),
    )
    data.update(changes)
    return CompanyIdentity(**data)


def authority() -> MailAuthority:
    return MailAuthority(
        identity="tristan",
        mailbox="corporate@tristan.example",
        permissions=("send_external",),
    )


def compliance(**changes) -> ComplianceContext:
    data = dict(
        message_class=MessageClass.E3_OFFICIAL_NONCOMMERCIAL,
        commercial=False,
        sender_identified=True,
        contact_information_present=True,
        ip_reviewed=True,
    )
    data.update(changes)
    return ComplianceContext(**data)


def test_message_hash_is_deterministic():
    first = draft()
    second = OfficialMessageDraft.from_mapping(first.canonical_payload())
    assert first.content_hash == second.content_hash
    assert first.content_hash.startswith("sha256:")


def test_conceptual_company_is_blocked_in_production():
    record = company(
        state=CompanyState.IDEA,
        legal_name=None,
        legal_identity_verified=False,
        external_send_enabled=False,
    )
    report = OfficializationGate().evaluate(
        company=record,
        draft=draft(),
        authority=authority(),
        compliance=compliance(),
        approval=None,
        production=True,
    )
    assert report.decision == OfficialDecision.BLOCK
    assert "company_not_legally_registered" in report.reasons


def test_only_missing_approval_returns_require_approval():
    message = draft()
    report = OfficializationGate().evaluate(
        company=company(),
        draft=message,
        authority=authority(),
        compliance=compliance(),
        approval=None,
        production=True,
    )
    assert report.decision == OfficialDecision.REQUIRE_APPROVAL
    assert report.reasons == ("human_approval_missing",)


def test_approval_is_bound_to_exact_content_hash():
    original = draft()
    approval = ApprovalRecord.create(
        original,
        approver="Tristan",
        approved_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
    )
    changed = draft("Objet modifié après approbation")
    report = OfficializationGate().evaluate(
        company=company(),
        draft=changed,
        authority=authority(),
        compliance=compliance(),
        approval=approval,
        production=True,
    )
    assert report.decision == OfficialDecision.BLOCK
    assert "approval_hash_or_scope_mismatch" in report.reasons


def test_commercial_message_requires_consent_and_unsubscribe():
    message = draft()
    approval = ApprovalRecord.create(message, approver="Tristan")
    report = OfficializationGate().evaluate(
        company=company(),
        draft=message,
        authority=authority(),
        compliance=compliance(
            message_class=MessageClass.E4_INDIVIDUAL_COMMERCIAL,
            commercial=True,
            consent_basis=None,
            consent_evidence_id=None,
            unsubscribe_present=False,
        ),
        approval=approval,
        production=True,
    )
    assert report.decision == OfficialDecision.BLOCK
    assert "commercial_consent_evidence_missing" in report.reasons
    assert "unsubscribe_mechanism_missing" in report.reasons


def test_verified_one_message_can_pass():
    message = draft()
    approval = ApprovalRecord.create(message, approver="Tristan")
    report = OfficializationGate().evaluate(
        company=company(),
        draft=message,
        authority=authority(),
        compliance=compliance(),
        approval=approval,
        production=True,
    )
    assert report.decision == OfficialDecision.ALLOW_ONE_MESSAGE
    assert report.allowed


def test_dry_run_never_uses_network():
    message = draft()
    report = OfficializationGate().evaluate(
        company=company(),
        draft=message,
        authority=authority(),
        compliance=compliance(),
        production=False,
    )
    receipt = deliver_one(
        report=report,
        draft=message,
        execute=False,
        provider=DryRunProvider(),
    )
    assert receipt.status == "DRY_RUN"
    assert "No network" in receipt.detail


def test_smtp_provider_requires_explicit_ack_and_allowlist(monkeypatch):
    monkeypatch.delenv("OMEGA_MAIL_EXTERNAL_SEND", raising=False)
    monkeypatch.setenv("OMEGA_MAIL_ALLOWED_RECIPIENT", "known.partner@example.net")
    provider = SMTPProvider(
        SMTPConfig(
            host="localhost",
            port=465,
            username="user",
            password="secret",
        )
    )
    with pytest.raises(RuntimeError, match="acknowledgement"):
        provider.send(draft())
