from __future__ import annotations

import json
from dataclasses import replace

import pytest

from omega_github_revenue_t import (
    AppendOnlyLedger,
    Artifact,
    DisclosureClass,
    Evidence,
    Experiment,
    ExperimentDecision,
    OAKStatus,
    RevenueEvent,
    RevenuePath,
    SensitiveDataError,
    SponsorTier,
    allocate_capital,
    assess_sponsor_tier,
    compile_offer,
    decide_experiment,
    evaluate_artifact,
    stream_frontier,
)


def artifact(**overrides):
    base = Artifact(
        artifact_id="OAKGATE-001",
        title="OAKGate Repository Audit",
        problem="Teams need reproducible repository quality evidence.",
        actor="authorized repository owner",
        oak_status=OAKStatus.DEMONSTRATED,
        disclosure=DisclosureClass.OPEN_PUBLIC,
        revenue_paths=(RevenuePath.FIXED_SCOPE_SERVICE, RevenuePath.GITHUB_APP),
        evidence=Evidence(
            tests=24,
            reproducible_demo=True,
            benchmark=True,
            limitations_documented=True,
        ),
        utility=0.9,
        reuse=0.8,
        discoverability=0.7,
        trust=0.8,
        conversion_clarity=0.85,
        noise=0.1,
        maintenance_burden=0.35,
        ip_legal_risk=0.1,
        safety_privacy_risk=0.2,
        next_action="run a consented pilot",
    )
    return replace(base, **overrides)


def test_demonstrated_artifact_is_offer_ready():
    result = evaluate_artifact(artifact())
    assert result["public_ready"] is True
    assert result["offer_ready"] is True
    assert 0 < result["score"] <= 1
    assert result["observed_revenue"] is False


def test_paying_user_is_only_an_observed_revenue_flag():
    candidate = artifact(evidence=replace(artifact().evidence, paying_user=True))
    result = evaluate_artifact(candidate)
    assert result["observed_revenue"] is True
    assert result["score"] <= 1


def test_disclosure_gate_fails_closed_for_patent_candidate():
    result = evaluate_artifact(artifact(disclosure=DisclosureClass.PATENT_CANDIDATE))
    assert result["public_ready"] is False
    assert "PATENT_CANDIDATE" in result["public_gate_reason"]


def test_public_after_review_requires_explicit_approval():
    candidate = artifact(disclosure=DisclosureClass.PUBLIC_AFTER_REVIEW)
    assert evaluate_artifact(candidate)["public_ready"] is False
    assert evaluate_artifact(candidate, review_approved=True)["public_ready"] is True


def test_offer_compiler_bounds_scope_and_rejects_unlimited_work():
    offer = compile_offer(artifact())
    assert offer.sustainable is True
    assert any("unlimited custom work" in item for item in offer.exclusions)
    weak = compile_offer(artifact(maintenance_burden=0.95))
    assert weak.sustainable is False


def test_sponsor_tier_sustainability():
    tier = SponsorTier(
        name="Research Follower",
        monthly_minor=1500,
        currency="USD",
        monthly_delivery_minutes=5,
        benefits=("public progress note",),
    )
    assert assess_sponsor_tier(tier)["sustainable"] is True
    unsafe = replace(tier, unlimited_custom_work=True)
    assert assess_sponsor_tier(unsafe)["sustainable"] is False


@pytest.mark.parametrize(
    ("experiment", "expected"),
    [
        (
            Experiment("e1", "pilot", "paid_audits", 1, 0, 3, 1),
            ExperimentDecision.CONTINUE,
        ),
        (
            Experiment("e2", "pilot", "paid_audits", 2, 3, 3, 3),
            ExperimentDecision.SCALE,
        ),
        (
            Experiment("e3", "pilot", "paid_audits", 2, 1.5, 3, 3),
            ExperimentDecision.REVISE,
        ),
        (
            Experiment("e4", "pilot", "paid_audits", 2, 0, 3, 3),
            ExperimentDecision.STOP,
        ),
        (
            Experiment("e5", "pilot", "paid_audits", 2, 3, 3, 3, hard_failure=True),
            ExperimentDecision.STOP,
        ),
    ],
)
def test_experiment_decisions(experiment, expected):
    assert decide_experiment(experiment) is expected


def test_sensitive_banking_fields_are_rejected(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(SensitiveDataError):
        ledger.append({"event_id": "x", "account_number": "never-store-this"})
    assert not (tmp_path / "ledger.jsonl").exists()


def test_revenue_event_and_hash_chain(tmp_path):
    event = RevenueEvent(
        event_id="rev-1",
        source="github_sponsors",
        gross_minor=500,
        fee_minor=0,
        currency="USD",
        occurred_at="2026-08-02T00:00:00Z",
    )
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    first = ledger.append(event.to_dict())
    second = ledger.append({**event.to_dict(), "event_id": "rev-2"})
    assert second["previous_hash"] == first["record_hash"]
    assert ledger.verify() == (True, 2, None)


def test_hash_chain_detects_tampering(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = AppendOnlyLedger(path)
    ledger.append({"event_id": "rev-1", "gross_minor": 100, "currency": "CAD"})
    record = json.loads(path.read_text(encoding="utf-8"))
    record["payload"]["gross_minor"] = 999999
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    valid, line, reason = ledger.verify()
    assert valid is False
    assert line == 1
    assert reason == "record hash mismatch"


def test_stream_frontier_is_lazy_and_has_no_fixed_item_ceiling():
    template = artifact().to_dict()

    def records():
        for index in range(12001):
            yield {**template, "artifact_id": f"A-{index}"}

    iterator = stream_frontier(records(), minimum_score=0.1)
    first = next(iterator)
    assert first["index"] == 0
    count = 1 + sum(1 for _ in iterator)
    assert count == 12001


def test_capital_allocation_is_evidence_weighted_and_budget_bounded():
    strong = artifact(artifact_id="STRONG")
    weak = artifact(
        artifact_id="WEAK",
        oak_status=OAKStatus.EXPLORATORY,
        evidence=Evidence(),
        utility=0.2,
        trust=0.2,
        conversion_clarity=0.2,
    )
    result = allocate_capital(((weak, 1000), (strong, 1000)), available_minor=1200)
    assert result[0]["artifact_id"] == "STRONG"
    assert sum(item["granted_minor"] for item in result) == 1200
