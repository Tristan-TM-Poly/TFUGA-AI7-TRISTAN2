from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_discovery_kernel_t.frontier_conductor import (
    CORE_LOOP_WIDTH,
    ConductorLedger,
    ConductorPolicy,
    Decision,
    FrontierObservation,
    ResourceEnvelope,
    build_plan,
    decide_next,
    project_generator_campaign,
    read_plan,
    write_plan,
)


def envelope() -> ResourceEnvelope:
    return ResourceEnvelope(
        wall_time_seconds=2_000,
        writable_bytes=3_500_000_000,
        rss_soft_bytes=512_000_000,
        rollback_reserve_bytes=100_000_000,
        minimum_throughput_events_per_second=5_000,
        maximum_error_rate=0.0,
        maximum_batch_latency_seconds=1.0,
    )


def policy() -> ConductorPolicy:
    return ConductorPolicy(
        initial_events=1_000_000,
        growth_factor=2.0,
        target_events_per_partition=250_000,
        maximum_parallelism_hint=64,
        validation_sample_ppm=10_000,
        bytes_per_event_estimate=160.0,
        throughput_estimate_events_per_second=20_000,
        stage_time_overhead_seconds=2.0,
        interruption_fraction=0.524288,
    )


def observation(plan, stage_index=0, **overrides) -> FrontierObservation:
    stage = plan.stages[stage_index]
    values = dict(
        plan_id=plan.plan_id,
        stage_index=stage_index,
        attempted_events=stage.target_events,
        accepted_events=stage.target_events,
        elapsed_seconds=stage.target_events / 20_000,
        bytes_written=stage.target_events * 150,
        peak_rss_bytes=200_000_000,
        maximum_batch_latency_seconds=0.25,
        error_count=0,
        duplicate_count=0,
        orphan_parent_count=0,
        complete_subjects=stage.target_subjects,
        interrupted_and_resumed=True,
        ledger_digest="a" * 64,
        observed_at="2026-08-02T19:30:00Z",
    )
    values.update(overrides)
    return FrontierObservation(**values)


def test_resource_plan_grows_geometrically_without_total_cap() -> None:
    plan = build_plan(envelope(), policy())
    assert plan.validate() == []
    assert plan.stage_count >= 4
    assert [stage.target_events for stage in plan.stages[:4]] == [
        1_000_000,
        2_000_000,
        4_000_000,
        8_000_000,
    ]
    assert plan.planned_events > 10_000_000
    assert plan.no_permanent_total_event_cap is True
    assert not hasattr(plan.policy, "max_total_events")
    assert not hasattr(plan.envelope, "max_total_events")


def test_all_stages_and_partitions_are_closed_loop_aligned() -> None:
    plan = build_plan(envelope(), policy())
    for stage in plan.stages:
        assert stage.target_events % CORE_LOOP_WIDTH == 0
        assert stage.target_subjects * CORE_LOOP_WIDTH == stage.target_events
        assert sum(part.event_count for part in stage.partitions) == stage.target_events
        assert all(part.event_count % CORE_LOOP_WIDTH == 0 for part in stage.partitions)
        assert stage.forced_interrupt_after % CORE_LOOP_WIDTH == 0
        assert 0 < stage.forced_interrupt_after < stage.target_events


def test_plan_stops_at_real_resource_envelope() -> None:
    constrained = ResourceEnvelope(
        wall_time_seconds=70,
        writable_bytes=400_000_000,
        rss_soft_bytes=256_000_000,
        rollback_reserve_bytes=50_000_000,
        minimum_throughput_events_per_second=1_000,
    )
    plan = build_plan(constrained, policy())
    assert plan.stage_count == 1
    assert plan.exhausted_resource in {"wall_time_seconds", "writable_bytes"}
    assert plan.stages[-1].cumulative_seconds <= constrained.wall_time_seconds
    assert plan.stages[-1].cumulative_bytes <= constrained.payload_budget_bytes


def test_plan_round_trip_and_fingerprint_detect_tampering(tmp_path: Path) -> None:
    plan = build_plan(envelope(), policy())
    path = tmp_path / "plan.json"
    write_plan(plan, path)
    restored = read_plan(path)
    assert restored.plan_id == plan.plan_id
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["stages"][0]["target_events"] += 8
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid frontier plan"):
        read_plan(path)


def test_clean_observation_expands() -> None:
    plan = build_plan(envelope(), policy())
    decision = decide_next(plan, observation(plan))
    assert decision.decision is Decision.EXPAND
    assert decision.next_target_events == 2_000_000
    assert decision.m_minus == ()


def test_memory_or_latency_saturation_reshards_and_records_negative_memory() -> None:
    plan = build_plan(envelope(), policy())
    decision = decide_next(
        plan,
        observation(
            plan,
            peak_rss_bytes=700_000_000,
            maximum_batch_latency_seconds=2.5,
        ),
    )
    assert decision.decision is Decision.RESHARD
    assert decision.recommended_partition_events == 125_000
    assert {item.saturation_kind for item in decision.m_minus} == {"rss", "batch_latency"}


def test_integrity_failure_forces_redesign() -> None:
    plan = build_plan(envelope(), policy())
    decision = decide_next(
        plan,
        observation(plan, duplicate_count=2, orphan_parent_count=1),
    )
    assert decision.decision is Decision.REDESIGN
    assert decision.next_target_events == plan.stages[0].target_events
    assert {item.saturation_kind for item in decision.m_minus} >= {"duplicate_ids", "orphan_parents"}


def test_missing_resume_proof_holds_scale() -> None:
    plan = build_plan(envelope(), policy())
    decision = decide_next(plan, observation(plan, interrupted_and_resumed=False))
    assert decision.decision is Decision.HOLD
    assert any(item.saturation_kind == "resume_proof" for item in decision.m_minus)


def test_ledger_is_exactly_once_hash_chained_and_resumable(tmp_path: Path) -> None:
    plan = build_plan(envelope(), policy())
    obs = observation(plan)
    decision = decide_next(plan, obs)
    ledger = ConductorLedger(tmp_path)
    assert ledger.append(obs, decision) is True
    assert ledger.append(obs, decision) is False
    audit = ledger.audit()
    assert audit["status"] == "PASS"
    assert audit["entries"] == 1
    assert audit["observations"] == 1
    assert len(audit["chain_digest"]) == 64
    resumed = ConductorLedger(tmp_path)
    assert resumed.next_sequence == 1
    assert resumed.append(obs, decision) is False


def test_ledger_persists_mminus_and_detects_tampering(tmp_path: Path) -> None:
    plan = build_plan(envelope(), policy())
    obs = observation(plan, duplicate_count=1)
    decision = decide_next(plan, obs)
    ledger = ConductorLedger(tmp_path)
    ledger.append(obs, decision)
    assert ledger.audit()["m_minus_records"] >= 1
    lines = (tmp_path / "conductor-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    entry["observation"]["accepted_events"] -= 8
    (tmp_path / "conductor-ledger.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        ConductorLedger(tmp_path)


def test_generator_campaign_projection_maps_every_record_to_one_closed_loop() -> None:
    projection = project_generator_campaign({
        "planned_logical_records": 1_179_648_000,
        "epoch_count": 1_000,
        "partition_count": 8_000,
        "no_permanent_total_addition_cap": True,
    })
    assert projection.projected_discovery_subjects == 1_179_648_000
    assert projection.projected_discovery_events == 9_437_184_000
    assert len(projection.projection_digest) == 64


def test_generator_projection_rejects_false_no_cap_claim() -> None:
    with pytest.raises(ValueError, match="permanent cap"):
        project_generator_campaign({
            "planned_logical_records": 100,
            "epoch_count": 1,
            "partition_count": 1,
            "no_permanent_total_addition_cap": False,
        })


def test_observation_requires_exact_closed_loop_alignment() -> None:
    plan = build_plan(envelope(), policy())
    with pytest.raises(ValueError, match="closed-loop aligned"):
        observation(plan, accepted_events=999_999)


def test_large_resource_envelope_plans_beyond_billion_without_materialization() -> None:
    huge = ResourceEnvelope(
        wall_time_seconds=1_000_000,
        writable_bytes=10_000_000_000_000,
        rss_soft_bytes=4_000_000_000,
        rollback_reserve_bytes=1_000_000_000,
        minimum_throughput_events_per_second=1_000,
    )
    p = ConductorPolicy(
        initial_events=1_000_000,
        growth_factor=2.0,
        target_events_per_partition=10_000_000,
        bytes_per_event_estimate=100.0,
        throughput_estimate_events_per_second=100_000.0,
    )
    plan = build_plan(huge, p)
    assert plan.planned_events > 1_000_000_000
    assert plan.stage_count < 100
    assert plan.validate() == []
