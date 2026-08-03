from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from omega_company_outreach_t.cli import append_case, audit_ledger, case_from_mapping
from omega_company_outreach_t.dashboard import build_dashboard
from omega_company_outreach_t.inbound import PrivateMailMetadata, build_public_event, classify_reply
from omega_company_outreach_t.models import (
    CompanyUnit,
    ConsentBasis,
    MailEventType,
    NextAction,
    OutreachCase,
    OutreachKind,
    OutreachStatus,
    PublicMailEvent,
    ReplyClass,
    RiskTier,
    StrategicSignals,
    hmac_sha256_text,
)
from omega_company_outreach_t.policy import (
    OutreachBudget,
    company_signature,
    follow_up_allowed,
    next_action_for_event,
    validate_policy,
    validate_portfolio,
)
from omega_company_outreach_t.scoring import score_case


def make_case(**overrides):
    values = dict(
        case_id="OUT-2026-TEST",
        company_unit=CompanyUnit.PARENT,
        kind=OutreachKind.ENTREPRENEURSHIP,
        target_organization="Example",
        recipient_hash="sha256:" + "a" * 64,
        subject="Exploratory discussion",
        purpose="Explore a non-binding program fit.",
        status=OutreachStatus.SENT,
        sent_at="2026-08-02",
        provider_receipt_hash="sha256:" + "b" * 64,
        source_issue=278,
    )
    values.update(overrides)
    return OutreachCase(**values)


def make_event(reply_class=ReplyClass.POSITIVE, event_type=MailEventType.REPLY):
    return PublicMailEvent(
        event_id="EVT-2026-TEST",
        case_id="OUT-2026-TEST",
        event_type=event_type,
        message_hash="hmac-sha256:" + "a" * 64,
        thread_hash="hmac-sha256:" + "b" * 64,
        counterparty_hash="hmac-sha256:" + "c" * 64,
        occurred_at="2026-08-03T12:00:00+00:00",
        reply_class=reply_class,
        source_issue=278,
    )


def test_legacy_case_mapping_defaults():
    case = case_from_mapping(
        {
            "case_id": "OUT-1",
            "company_unit": "tristan_parent_opco",
            "kind": "entrepreneurship",
            "target_organization": "Example",
            "recipient_hash": "sha256:" + "a" * 64,
            "subject": "Hello",
            "purpose": "Exploratory",
            "status": "sent",
            "sent_at": "2026-08-02",
            "provider_receipt_hash": "sha256:" + "b" * 64,
            "source_issue": 278,
        }
    )
    assert case.consent_basis is ConsentBasis.NOT_COMMERCIAL
    assert case.risk_tier is RiskTier.LOW
    assert not validate_policy(case)


def test_commercial_message_requires_real_consent_and_unsubscribe():
    case = make_case(
        commercial_message=True,
        consent_basis=ConsentBasis.NONE,
        unsubscribe_required=False,
        unsubscribe_mechanism_verified=False,
    )
    errors = validate_policy(case)
    assert any("consent" in error for error in errors)
    assert any("unsubscribe" in error for error in errors)


def test_noncommercial_institutional_message_is_allowed():
    case = make_case(
        company_unit=CompanyUnit.RESEARCH,
        kind=OutreachKind.RESEARCH_PILOT,
        consent_basis=ConsentBasis.PUBLIC_INSTITUTIONAL_CONTACT,
    )
    assert not validate_policy(case)


def test_high_risk_is_blocked():
    case = make_case(risk_tier=RiskTier.HIGH)
    assert any("high-risk" in error for error in validate_policy(case))


def test_hmac_requires_secret_length():
    with pytest.raises(ValueError):
        hmac_sha256_text("x", "short")
    value = hmac_sha256_text("x", "0123456789abcdef")
    assert value.startswith("hmac-sha256:")
    assert len(value) == 76


@pytest.mark.parametrize(
    ("subject", "snippet", "expected"),
    [
        ("Réponse automatique", "Je suis en congé, retour le 10 août", ReplyClass.AUTO_REPLY),
        ("Delivery Status Notification", "Undeliverable", ReplyClass.BOUNCE),
        ("Please unsubscribe", "Remove me", ReplyClass.UNSUBSCRIBE),
        ("Re: Pilot", "Please send your budget and documentation", ReplyClass.INFORMATION_REQUEST),
        ("Re: Pilot", "Please contact my colleague, the right person", ReplyClass.REFERRAL),
        ("Re: Pilot", "Yes, we are interested in a meeting", ReplyClass.POSITIVE),
        ("Re: Pilot", "We are not interested", ReplyClass.DECLINE),
        ("Re: Pilot", "Thank you for the note", ReplyClass.UNKNOWN),
    ],
)
def test_reply_classifier(subject, snippet, expected):
    assert classify_reply(subject, snippet) is expected


def test_public_event_drops_raw_content():
    private = PrivateMailMetadata(
        case_id="OUT-2026-TEST",
        provider_message_id="gmail-message-id",
        provider_thread_id="gmail-thread-id",
        counterparty="person@example.com",
        occurred_at="2026-08-03T12:00:00+00:00",
        subject="Re: Pilot",
        snippet="Yes, interested in a meeting",
        source_issue=278,
    )
    event = build_public_event(private, secret="0123456789abcdef", event_id="EVT-2026-TEST")
    payload = json.dumps(event.public_mapping())
    assert "person@example.com" not in payload
    assert "gmail-message-id" not in payload
    assert "interested in a meeting" not in payload
    assert event.reply_class is ReplyClass.POSITIVE
    assert not event.validate()


@pytest.mark.parametrize(
    ("reply_class", "event_type", "expected"),
    [
        (ReplyClass.POSITIVE, MailEventType.REPLY, NextAction.PREPARE_MEETING),
        (ReplyClass.INFORMATION_REQUEST, MailEventType.REPLY, NextAction.PREPARE_EVIDENCE),
        (ReplyClass.REFERRAL, MailEventType.REPLY, NextAction.REVIEW_REFERRAL),
        (ReplyClass.AUTO_REPLY, MailEventType.AUTO_REPLY, NextAction.WAIT),
        (ReplyClass.BOUNCE, MailEventType.BOUNCE, NextAction.CORRECT_ADDRESS),
        (ReplyClass.DECLINE, MailEventType.REPLY, NextAction.CLOSE),
        (ReplyClass.UNSUBSCRIBE, MailEventType.UNSUBSCRIBE, NextAction.CLOSE),
        (ReplyClass.UNKNOWN, MailEventType.REPLY, NextAction.HUMAN_REVIEW),
    ],
)
def test_next_action(reply_class, event_type, expected):
    assert next_action_for_event(make_event(reply_class, event_type)) is expected


def test_strategic_scoring_high_and_low():
    case = make_case()
    high = score_case(
        case,
        StrategicSignals(
            relevance=5,
            decision_authority=5,
            problem_fit=5,
            evidence_readiness=5,
            timing=5,
            reciprocity=4,
            effort=1,
            risk=1,
        ),
    )
    assert high.score >= 75
    assert high.disposition == "send_or_continue"

    low = score_case(
        case,
        StrategicSignals(
            relevance=1,
            decision_authority=0,
            problem_fit=1,
            evidence_readiness=1,
            timing=0,
            reciprocity=0,
            effort=5,
            risk=5,
        ),
    )
    assert low.score < 35
    assert low.disposition == "hold"


def test_follow_up_guard():
    case = make_case()
    sent = datetime(2026, 8, 2, tzinfo=timezone.utc)
    assert not follow_up_allowed(case, sent, now=datetime(2026, 8, 10, tzinfo=timezone.utc))
    assert follow_up_allowed(case, sent, now=datetime(2026, 8, 17, tzinfo=timezone.utc))
    assert not follow_up_allowed(
        case,
        sent,
        now=datetime(2026, 8, 17, tzinfo=timezone.utc),
        unanswered_followups=1,
    )


def test_portfolio_quotas():
    cases = [
        make_case(case_id=f"OUT-{i}", provider_receipt_hash="sha256:" + f"{i:064x}")
        for i in range(6)
    ]
    errors = validate_portfolio(
        cases,
        now=datetime(2026, 8, 2, 18, tzinfo=timezone.utc),
        budget=OutreachBudget(maximum_daily_sends=5),
    )
    assert "maximum daily external sends exceeded" in errors
    assert any("organization quota" in error for error in errors)


def test_ledger_chain_and_tamper(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    append_case(make_case(), ledger)
    assert not audit_ledger(ledger)
    text = ledger.read_text()
    ledger.write_text(text.replace("Exploratory", "Altered"))
    assert any("hash mismatch" in error for error in audit_ledger(ledger))


def test_company_signature_is_truthful():
    signature = company_signature(CompanyUnit.RESEARCH)
    assert "Tristan Research Foundry" in signature
    assert "non présenté comme entité constituée" in signature


def test_dashboard_counts():
    cases = [make_case()]
    events = [make_event()]
    dashboard = build_dashboard(cases, events, generated_at="2026-08-02T22:00:00+00:00")
    payload = dashboard.as_dict()
    assert payload["totals"]["cases"] == 1
    assert payload["next_actions"]["prepare_meeting"] == 1
    assert "Ω Company Outreach Dashboard" in dashboard.as_markdown()
