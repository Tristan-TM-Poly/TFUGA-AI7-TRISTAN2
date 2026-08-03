import json
from dataclasses import replace

import pytest

from omega_hqt_t.r02.campaign import (
    all_fixtures,
    compare_models,
    compile_public_evidence_mission,
    demand_fixture,
    run_r02_benchmark,
)
from omega_hqt_t.r02.evidence import (
    assess_composability_risk,
    build_snapshot,
    compile_descriptive_claims,
    detect_claim_contradictions,
    diff_snapshots,
)
from omega_hqt_t.r02.ingest import ingest_text


def test_r02_benchmark_certifies_all_boundaries():
    report = run_r02_benchmark(hours=8)
    assert report.passed
    assert all(report.checks.values())
    assert report.status == "CERTIFIED_OFFLINE_PUBLIC_EVIDENCE_FIXTURES_R0_2"
    assert report.claims["real_grid_validated"] is False
    assert report.claims["operational_use_authorized"] is False


def test_claims_retain_observation_evidence():
    source, text = demand_fixture(hours=3)
    observations = ingest_text(text, "json", source).observations
    claims = compile_descriptive_claims(observations)
    assert claims
    assert all(claim.evidence_ids for claim in claims)
    assert all(claim.scope == "supplied_offline_fixture_only" for claim in claims)


def test_numeric_contradiction_is_first_class():
    source, text = demand_fixture(hours=3)
    claim = compile_descriptive_claims(ingest_text(text, "json", source).observations)[0]
    conflicting = replace(claim, claim_id="conflict", object_value="999999 MW")
    contradictions = detect_claim_contradictions((claim, conflicting))
    assert len(contradictions) == 1
    assert contradictions[0].kind == "NUMERIC_CONFLICT"


def test_fixture_ingest_is_deterministic_and_deduplicated():
    source, text = demand_fixture(hours=2)
    first = ingest_text(text, "json", source)
    second = ingest_text(text, "json", source)
    assert first.receipt == second.receipt
    assert len(first.observations) == 8
    assert not first.quarantine


def test_invalid_and_prohibited_record_is_quarantined():
    source, _ = demand_fixture(hours=1)
    record = [{
        "variable": "demand",
        "value": "nan",
        "unit": "MW",
        "observed_at": "bad",
        "region_id": "x",
        "credential": "secret",
    }]
    result = ingest_text(json.dumps(record), "json", source)
    assert not result.observations
    assert result.quarantine
    assert any("PROHIBITED_FIELD_CREDENTIAL" in item.reason_codes for item in result.quarantine)


def test_unknown_licence_is_blocked():
    source, text = demand_fixture(hours=1)
    blocked = replace(source, licence_id="unknown")
    with pytest.raises(PermissionError):
        ingest_text(text, "json", blocked)


def test_model_disagreement_is_explicit_and_hashed():
    source, text = demand_fixture(hours=6)
    reports = compare_models(ingest_text(text, "json", source).observations)
    assert reports
    assert all(report.spread >= 0 for report in reports)
    assert all(len(report.evidence_hash) == 64 for report in reports)


def test_public_mission_is_compiled():
    mission = compile_public_evidence_mission("Compare regional public energy indicators")
    assert mission.status.startswith("READY")
    assert "network crawling" in mission.forbidden_actions


def test_operational_mission_is_blocked():
    mission = compile_public_evidence_mission("Issue a SCADA control command")
    assert mission.status.startswith("BLOCKED")


def test_fixture_composability_is_scored_not_ignored():
    sources = []
    observations = []
    for source, text, fmt in all_fixtures(hours=4):
        result = ingest_text(text, fmt, source)
        sources.append(source)
        observations.extend(result.observations)
    assessment = assess_composability_risk(sources, observations)
    assert 0 <= assessment.composability_risk <= 1
    assert assessment.decision in {"PUBLIC_AGGREGATED_RESEARCH_ONLY", "HUMAN_REVIEW_REQUIRED"}
    assert "human review before publication" in assessment.controls


def test_snapshot_diff_detects_append_only_change():
    source, text = demand_fixture(hours=2)
    observations = ingest_text(text, "json", source).observations
    before = build_snapshot(observations[:-1], "2026-08-03T19:00:00Z")
    after = build_snapshot(observations, "2026-08-03T20:00:00Z", before.snapshot_id)
    diff = diff_snapshots(before, after, observations[:-1], observations)
    assert len(diff.added_observation_ids) == 1
    assert not diff.removed_observation_ids
    assert len(diff.evidence_hash) == 64
