from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from omega_company_outreach_t.cli import append_case, audit_ledger
from omega_company_outreach_t.models import CompanyUnit, OutreachCase, OutreachKind, OutreachStatus
from omega_company_outreach_t.policy import disclosure_line, follow_up_allowed, route_kind, validate_policy


def case(**overrides):
    payload = {
        "case_id": "OUT-2026-TEST1",
        "company_unit": CompanyUnit.PARENT,
        "kind": OutreachKind.ENTREPRENEURSHIP,
        "target_organization": "Example Organization",
        "recipient_hash": "sha256:" + "a" * 64,
        "subject": "Exploratory program request",
        "purpose": "Request non-binding program guidance.",
        "status": OutreachStatus.SENT,
        "sent_at": "2026-08-02",
        "provider_receipt_hash": "sha256:" + "b" * 64,
        "source_issue": 278,
        "follow_up_after": "2026-08-16",
        "legal_entity_claimed": False,
        "corporate_domain_verified": False,
    }
    payload.update(overrides)
    return OutreachCase(**payload)


def test_valid_sent_case():
    assert validate_policy(case()) == []


def test_legal_entity_claim_requires_verified_state_and_domain():
    errors = validate_policy(case(legal_entity_claimed=True))
    assert any("verified corporate domain" in error for error in errors)
    assert any("not a verified incorporated legal entity" in error for error in errors)


def test_company_kind_routing():
    assert route_kind(OutreachKind.ENTREPRENEURSHIP) is CompanyUnit.PARENT
    assert route_kind(OutreachKind.SOFTWARE_PILOT) is CompanyUnit.SOFTWARE
    assert route_kind(OutreachKind.RESEARCH_PILOT) is CompanyUnit.RESEARCH
    assert route_kind(OutreachKind.GOVERNANCE) is CompanyUnit.OAK


def test_nonincorporated_disclosure_is_explicit():
    line = disclosure_line(CompanyUnit.RESEARCH)
    assert "non présenté comme entité constituée" in line


def test_follow_up_cooldown():
    prior = datetime(2026, 8, 2, tzinfo=timezone.utc)
    before = datetime(2026, 8, 10, tzinfo=timezone.utc)
    after = datetime(2026, 8, 17, tzinfo=timezone.utc)
    assert not follow_up_allowed(case(), prior, now=before)
    assert follow_up_allowed(case(), prior, now=after)
    assert follow_up_allowed(case(), prior, now=before, new_event=True)


def test_ledger_round_trip_and_replay_block(tmp_path: Path):
    ledger = tmp_path / "outreach.jsonl"
    first = append_case(case(), ledger)
    assert first["sequence"] == 1
    assert audit_ledger(ledger) == []
    with pytest.raises(ValueError, match="case already exists"):
        append_case(case(), ledger)


def test_ledger_detects_tampering(tmp_path: Path):
    ledger = tmp_path / "outreach.jsonl"
    append_case(case(), ledger)
    entry = json.loads(ledger.read_text(encoding="utf-8"))
    entry["case"]["target_organization"] = "Tampered"
    ledger.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    assert "entry 1: hash mismatch" in audit_ledger(ledger)


def test_forbidden_financial_instruction_is_blocked():
    errors = validate_policy(case(purpose="Please change banking coordinates by email."))
    assert any("change banking" in error for error in errors)


def test_wrong_company_kind_is_blocked():
    errors = validate_policy(case(company_unit=CompanyUnit.RESEARCH, kind=OutreachKind.ENTREPRENEURSHIP))
    assert any("not allowed" in error for error in errors)
