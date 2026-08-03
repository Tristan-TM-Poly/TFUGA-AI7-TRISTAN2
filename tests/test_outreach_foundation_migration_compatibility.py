from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from omega_company_outreach_t.foundation.canonical import CanonicalizationError
from omega_company_outreach_t.foundation.contacts import RoleCategory
from omega_company_outreach_t.foundation.consent import ConsentBasis, ConsentScope
from omega_company_outreach_t.foundation.migration import MigrationIds
from omega_company_outreach_t.foundation.migration_runtime import migrate_case_file
from omega_company_outreach_t.foundation.opportunities import OpportunityType, StrategicSignals
from omega_company_outreach_t.foundation.organizations import OrganizationType

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def ids() -> MigrationIds:
    return MigrationIds(
        organization_id="ORG-2026-0041",
        contact_id="CNT-2026-0041",
        consent_id="CONSENT-2026-0041",
        opportunity_id="OPP-2026-0041",
        evidence_id="EVID-2026-0041",
        contact_evidence_id="EVID-2026-5041",
        event_ids=tuple(f"EVT-2026-04{index:02d}" for index in range(1, 6)),
    )


def signals() -> StrategicSignals:
    return StrategicSignals(
        relevance=0.9,
        authority=0.8,
        problem_fit=0.9,
        asset_readiness=0.8,
        evidence=0.8,
        timing=0.8,
        reciprocity=0.9,
        expected_value=0.8,
        probability_response=0.6,
        probability_conversion=0.4,
        optionality=0.9,
        effort_cost=0.2,
        legal_risk=0.1,
        reputation_risk=0.1,
        privacy_risk=0.1,
        maintenance_cost=0.2,
        opportunity_cost=0.2,
    )


def privacy_hardened_payload() -> dict[str, object]:
    return {
        "case_id": "OUT-2026-0041",
        "company_unit": "tristan_parent_opco",
        "purpose": "Request non-binding program guidance.",
        "sent_at": "2026-08-02",
        "recipient_hash": HASH_A,
        "provider_receipt_hash": HASH_B,
        "source_issue": 285,
        "legal_entity_claimed": False,
    }


def migrate(source: Path, destination: Path, *, organization_name: str | None):
    return migrate_case_file(
        source,
        destination,
        ids=ids(),
        organization_type=OrganizationType.NONPROFIT,
        opportunity_type=OpportunityType.ENTREPRENEURSHIP_PROGRAM,
        role_category=RoleCategory.PROGRAM_MANAGER,
        consent_basis=ConsentBasis.EXISTING_NONBUSINESS_RELATIONSHIP,
        consent_scope=ConsentScope.PROGRAM_INFORMATION,
        strategic_signals=signals(),
        proposed_asset_id="oakgate_company_validation",
        organization_domain="example.org",
        organization_name=organization_name,
    )


def test_privacy_hardened_case_requires_explicit_public_name(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(privacy_hardened_payload()), encoding="utf-8")
    with pytest.raises(CanonicalizationError, match="provide an explicit organization_name"):
        migrate(source, tmp_path / "out.json", organization_name=None)


def test_explicit_public_name_migrates_privacy_hardened_case(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(privacy_hardened_payload()), encoding="utf-8")
    result = migrate(source, tmp_path / "out.json", organization_name="Example Program")
    assert result["organization"]["canonical_name"] == "Example Program"
    assert result["migration_hash"].startswith("sha256:")


def test_explicit_name_cannot_conflict_with_legacy_name(tmp_path: Path):
    payload = privacy_hardened_payload()
    payload["target_organization"] = "Stored Organization"
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CanonicalizationError, match="conflicts"):
        migrate(source, tmp_path / "out.json", organization_name="Different Organization")


def test_explicit_name_may_confirm_same_legacy_name(tmp_path: Path):
    payload = privacy_hardened_payload()
    payload["target_organization"] = "Stored Organization"
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = migrate(source, tmp_path / "out.json", organization_name=" Stored  Organization ")
    assert result["organization"]["canonical_name"] == "Stored Organization"
