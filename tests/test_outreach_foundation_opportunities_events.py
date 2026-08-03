from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from omega_company_outreach_t.foundation.canonical import CanonicalizationError, canonical_hash
from omega_company_outreach_t.foundation.event_store import CanonicalEventStore
from omega_company_outreach_t.foundation.events import (
    AggregateType,
    DomainEvent,
    EventActor,
    EventType,
    build_outreach_projection,
)
from omega_company_outreach_t.foundation.opportunities import (
    CompanyUnit,
    Opportunity,
    OpportunityPosterior,
    OpportunityState,
    OpportunityType,
    PortfolioAction,
    PortfolioLimits,
    StrategicSignals,
    allocate_portfolio,
    audit_opportunities,
    recommend_action,
    route_opportunity,
)

NOW = datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def signals(**overrides):
    payload = {
        "relevance": 0.9,
        "authority": 0.8,
        "problem_fit": 0.9,
        "asset_readiness": 0.8,
        "evidence": 0.8,
        "timing": 0.8,
        "reciprocity": 0.9,
        "expected_value": 0.8,
        "probability_response": 0.6,
        "probability_conversion": 0.4,
        "optionality": 0.9,
        "effort_cost": 0.2,
        "legal_risk": 0.1,
        "reputation_risk": 0.1,
        "privacy_risk": 0.1,
        "maintenance_cost": 0.2,
        "opportunity_cost": 0.2,
    }
    payload.update(overrides)
    return StrategicSignals(**payload)


def opportunity(**overrides):
    payload = {
        "opportunity_id": "OPP-2026-0001",
        "organization_id": "ORG-2026-0001",
        "company_unit": CompanyUnit.SOFTWARE,
        "opportunity_type": OpportunityType.SOFTWARE_PILOT,
        "state": OpportunityState.QUALIFIED,
        "problem_statement": "A software team needs a verifiable repository audit pilot.",
        "proposed_asset_id": "oakgate_repository_audit",
        "evidence_hashes": (HASH_A,),
        "signals": signals(),
        "contact_id": "CNT-2026-0001",
        "source_issue": 285,
        "estimated_effort_hours": 6.0,
        "expected_value_cad": 2000,
        "created_at": NOW,
        "updated_at": NOW,
    }
    payload.update(overrides)
    return Opportunity(**payload)


def actor():
    return EventActor(
        actor_id="tristan",
        actor_type="founder",
        company_id="tristan_software_labs",
    )


def test_strategic_score_penalizes_risk_and_effort():
    strong = signals()
    risky = signals(
        legal_risk=0.9,
        reputation_risk=0.8,
        privacy_risk=0.8,
        effort_cost=0.9,
        maintenance_cost=0.8,
        opportunity_cost=0.8,
    )
    assert strong.score_100 > risky.score_100
    assert strong.positive_geometric_mean > 0
    assert risky.risk_burden > strong.risk_burden


@pytest.mark.parametrize("field", list(StrategicSignals.__dataclass_fields__))
def test_strategic_signals_reject_out_of_range_values(field):
    with pytest.raises(CanonicalizationError):
        signals(**{field: 1.01})


def test_posterior_updates_stage_without_mutating_prior():
    prior = OpportunityPosterior()
    posterior = prior.observe("response", success=True, weight=2.0)
    assert posterior.response.mean > prior.response.mean
    assert posterior.response.observations == 1
    assert prior.response.observations == 0


def test_posterior_expected_payment_is_product_of_stages():
    posterior = OpportunityPosterior()
    expected = (
        posterior.response.mean
        * posterior.meeting_given_response.mean
        * posterior.pilot_given_meeting.mean
        * posterior.payment_given_pilot.mean
    )
    assert posterior.expected_payment_probability == pytest.approx(expected)


def test_opportunity_hash_and_deduplication_are_stable():
    first = opportunity()
    second = opportunity(opportunity_id="OPP-2026-0002")
    assert first.opportunity_hash != second.opportunity_hash
    assert first.deduplication_key == second.deduplication_key


def test_opportunity_expected_pipeline_value_uses_posterior():
    item = opportunity(expected_value_cad=10000)
    assert item.expected_pipeline_value_cad == pytest.approx(
        10000 * item.posterior.expected_payment_probability
    )


def test_company_routing_covers_all_opportunity_types():
    for item in OpportunityType:
        assert isinstance(route_opportunity(item), CompanyUnit)
    assert route_opportunity(OpportunityType.SOFTWARE_PILOT) is CompanyUnit.SOFTWARE
    assert route_opportunity(OpportunityType.RESEARCH_PILOT) is CompanyUnit.RESEARCH
    assert route_opportunity(OpportunityType.AUDIT_SERVICE) is CompanyUnit.OAK
    assert route_opportunity(OpportunityType.FINANCING_PROGRAM) is CompanyUnit.PARENT


def test_audit_detects_wrong_company_route():
    wrong = opportunity(company_unit=CompanyUnit.RESEARCH)
    errors = audit_opportunities((wrong,))
    assert any("expected company" in error for error in errors)


def test_audit_detects_duplicate_opportunity_key():
    first = opportunity()
    second = opportunity(opportunity_id="OPP-2026-0002")
    errors = audit_opportunities((first, second))
    assert any("duplicate opportunity" in error for error in errors)


@pytest.mark.parametrize(
    "state,target",
    [
        (OpportunityState.DISCOVERED, OpportunityState.QUALIFIED),
        (OpportunityState.QUALIFIED, OpportunityState.ACTIVE),
        (OpportunityState.ACTIVE, OpportunityState.MEETING),
        (OpportunityState.MEETING, OpportunityState.PILOT),
        (OpportunityState.PILOT, OpportunityState.PROPOSAL),
        (OpportunityState.PROPOSAL, OpportunityState.NEGOTIATION),
        (OpportunityState.NEGOTIATION, OpportunityState.WON),
    ],
)
def test_valid_opportunity_transitions(state, target):
    item = opportunity(state=state)
    assert item.transition(target).state is target


def test_won_opportunity_is_terminal():
    item = opportunity(state=OpportunityState.WON)
    with pytest.raises(CanonicalizationError):
        item.transition(OpportunityState.ACTIVE)


def test_recommend_action_blocks_legal_risk():
    item = opportunity(signals=signals(legal_risk=0.9))
    assert recommend_action(item) is PortfolioAction.BLOCK


def test_recommend_action_requires_evidence():
    item = opportunity(
        state=OpportunityState.NEEDS_EVIDENCE,
        signals=signals(evidence=0.1),
    )
    assert recommend_action(item) is PortfolioAction.PREPARE_EVIDENCE


def test_recommend_action_builds_asset_before_outreach():
    item = opportunity(signals=signals(asset_readiness=0.2))
    assert recommend_action(item) is PortfolioAction.BUILD_ASSET_FIRST


def test_recommend_action_acts_on_high_score_active_case():
    item = opportunity(state=OpportunityState.ACTIVE)
    assert item.strategic_score >= 68
    assert recommend_action(item) is PortfolioAction.ACT_NOW


def test_portfolio_respects_effort_capacity_and_risk_limits():
    items = (
        opportunity(opportunity_id="OPP-2026-0001", estimated_effort_hours=6),
        opportunity(
            opportunity_id="OPP-2026-0002",
            organization_id="ORG-2026-0002",
            problem_statement="Another team needs a repository audit.",
            estimated_effort_hours=8,
            evidence_hashes=(HASH_B,),
        ),
        opportunity(
            opportunity_id="OPP-2026-0003",
            organization_id="ORG-2026-0003",
            problem_statement="A third team needs a high-risk audit.",
            estimated_effort_hours=8,
            signals=signals(privacy_risk=0.65),
        ),
        opportunity(
            opportunity_id="OPP-2026-0004",
            organization_id="ORG-2026-0004",
            problem_statement="A fourth team needs another high-risk audit.",
            estimated_effort_hours=8,
            signals=signals(reputation_risk=0.70),
        ),
    )
    selection = allocate_portfolio(
        items,
        PortfolioLimits(
            active_priority_cases=3,
            maximum_open_cases=4,
            high_risk_cases_in_parallel=1,
            effort_budget_hours=22,
            minimum_score=40,
        ),
    )
    assert len(selection.selected_ids) <= 3
    assert selection.total_effort_hours <= 22
    selected_high_risk = [
        item
        for item in items
        if item.opportunity_id in selection.selected_ids
        and max(
            item.signals.legal_risk,
            item.signals.privacy_risk,
            item.signals.reputation_risk,
        )
        >= 0.60
    ]
    assert len(selected_high_risk) <= 1
    assert selection.selection_hash == canonical_hash(selection)


def test_event_store_round_trip_and_projection(tmp_path: Path):
    store = CanonicalEventStore(tmp_path / "events.jsonl")
    first = store.append_new(
        event_id="EVT-2026-0001",
        event_type=EventType.OPPORTUNITY_CREATED,
        aggregate_type=AggregateType.OPPORTUNITY,
        aggregate_id="OPP-2026-0001",
        actor=actor(),
        occurred_at=NOW,
        payload={
            "projection": {
                "state": "qualified",
                "company_unit": "tristan_software_labs",
            },
            "opportunity_hash": HASH_A,
        },
        correlation_id="CORR-2026-0001",
        idempotency_key=HASH_A,
    )
    second = store.append_new(
        event_id="EVT-2026-0002",
        event_type=EventType.OPPORTUNITY_STATE_CHANGED,
        aggregate_type=AggregateType.OPPORTUNITY,
        aggregate_id="OPP-2026-0001",
        actor=actor(),
        occurred_at=NOW + timedelta(minutes=1),
        payload={"projection": {"state": "active"}},
        correlation_id="CORR-2026-0001",
        causation_id=first.event_id,
        idempotency_key=HASH_B,
    )
    assert second.previous_hash == first.event_hash
    audit = store.audit()
    assert audit.valid
    assert audit.event_count == 2
    assert audit.aggregate_count == 1
    events = store.read_all()
    assert events == (first, second)
    projection = build_outreach_projection(events)
    assert projection.opportunities["OPP-2026-0001"]["state"] == "active"
    assert projection.metrics["events"] == 2


def test_event_store_blocks_duplicate_idempotency(tmp_path: Path):
    store = CanonicalEventStore(tmp_path / "events.jsonl")
    store.append_new(
        event_id="EVT-2026-0001",
        event_type=EventType.MESSAGE_SENT,
        aggregate_type=AggregateType.OUTREACH_CASE,
        aggregate_id="OUT-2026-0001",
        actor=actor(),
        payload={"projection": {"state": "sent"}},
        occurred_at=NOW,
        idempotency_key=HASH_A,
    )
    with pytest.raises(CanonicalizationError, match="idempotency"):
        store.append_new(
            event_id="EVT-2026-0002",
            event_type=EventType.MESSAGE_SENT,
            aggregate_type=AggregateType.OUTREACH_CASE,
            aggregate_id="OUT-2026-0002",
            actor=actor(),
            payload={"projection": {"state": "sent"}},
            occurred_at=NOW,
            idempotency_key=HASH_A,
        )


def test_event_store_detects_tampering(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    store = CanonicalEventStore(path)
    store.append_new(
        event_id="EVT-2026-0001",
        event_type=EventType.MESSAGE_SENT,
        aggregate_type=AggregateType.OUTREACH_CASE,
        aggregate_id="OUT-2026-0001",
        actor=actor(),
        payload={"projection": {"state": "sent"}},
        occurred_at=NOW,
        idempotency_key=HASH_A,
    )
    row = json.loads(path.read_text(encoding="utf-8"))
    row["payload"]["projection"]["state"] = "tampered"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    audit = store.audit()
    assert not audit.valid
    assert any("event_hash mismatch" in error for error in audit.errors)


def test_event_store_refuses_append_after_tampering(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    store = CanonicalEventStore(path)
    store.append_new(
        event_id="EVT-2026-0001",
        event_type=EventType.MESSAGE_SENT,
        aggregate_type=AggregateType.OUTREACH_CASE,
        aggregate_id="OUT-2026-0001",
        actor=actor(),
        payload={"projection": {"state": "sent"}},
        occurred_at=NOW,
        idempotency_key=HASH_A,
    )
    path.write_text(path.read_text(encoding="utf-8").replace("sent", "fake"), encoding="utf-8")
    with pytest.raises(CanonicalizationError, match="invalid event store"):
        store.append_new(
            event_id="EVT-2026-0002",
            event_type=EventType.REPLY_RECEIVED,
            aggregate_type=AggregateType.OUTREACH_CASE,
            aggregate_id="OUT-2026-0001",
            actor=actor(),
            payload={"projection": {"state": "replied"}},
            occurred_at=NOW,
            idempotency_key=HASH_B,
        )


def test_event_store_snapshot_is_deterministic(tmp_path: Path):
    store = CanonicalEventStore(tmp_path / "events.jsonl")
    store.append_new(
        event_id="EVT-2026-0001",
        event_type=EventType.MESSAGE_SENT,
        aggregate_type=AggregateType.OUTREACH_CASE,
        aggregate_id="OUT-2026-0001",
        actor=actor(),
        payload={"projection": {"state": "sent"}},
        occurred_at=NOW,
        idempotency_key=HASH_A,
    )
    first = store.write_snapshot(tmp_path / "first.json", build_outreach_projection)
    second = store.write_snapshot(tmp_path / "second.json", build_outreach_projection)
    assert first == second
    assert (tmp_path / "first.json").read_bytes() == (tmp_path / "second.json").read_bytes()


def test_event_payload_rejects_secret_like_keys():
    with pytest.raises(CanonicalizationError, match="secret-like"):
        DomainEvent(
            event_id="EVT-2026-0001",
            event_type=EventType.MESSAGE_PREPARED,
            aggregate_type=AggregateType.MESSAGE,
            aggregate_id="MSG-2026-0001",
            sequence=1,
            occurred_at=NOW,
            actor=actor(),
            payload={"api_key": "not allowed"},
        )
