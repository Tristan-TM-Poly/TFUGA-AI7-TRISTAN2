from __future__ import annotations

from pathlib import Path
import time

from omega_discovery_kernel_t.frontier_conductor import (
    ConductorLedger,
    ConductorPolicy,
    Decision,
    FrontierObservation,
    ResourceEnvelope,
    build_plan,
    decide_next,
)
from omega_discovery_kernel_t.million_frontier import MillionFrontierConfig
from omega_discovery_kernel_t.million_optimized import run_forced_resume_million_frontier


def test_two_million_event_stage_promotes_to_four_million(tmp_path: Path) -> None:
    """Execute the next real frontier after R0.3 and feed it to the conductor."""

    plan = build_plan(
        ResourceEnvelope(
            wall_time_seconds=10_000,
            writable_bytes=20_000_000_000,
            rss_soft_bytes=8_000_000_000,
            rollback_reserve_bytes=1_000_000_000,
            minimum_throughput_events_per_second=100,
            maximum_error_rate=0.0,
            maximum_batch_latency_seconds=60.0,
        ),
        ConductorPolicy(
            initial_events=1_000_000,
            growth_factor=2.0,
            target_events_per_partition=500_000,
            maximum_parallelism_hint=16,
            bytes_per_event_estimate=250.0,
            throughput_estimate_events_per_second=5_000.0,
            stage_time_overhead_seconds=5.0,
            interruption_fraction=0.524288,
        ),
    )
    assert plan.stages[1].target_events == 2_000_000

    config = MillionFrontierConfig(
        target_events=2_000_000,
        forced_interrupt_after=1_048_576,
        seed=74,
        namespace_count=512,
        initial_shard_bytes=8 * 1024 * 1024,
        shard_growth_factor=1.7,
        checkpoint_interval=100_000,
        sqlite_batch_size=20_000,
        minimum_free_bytes=256 * 1024 * 1024,
        latency_saturation_seconds_per_10k=60.0,
        rss_saturation_bytes=8 * 1024 * 1024 * 1024,
    )
    output = tmp_path / "frontier-2m-r0-4"
    started = time.monotonic()
    summary = run_forced_resume_million_frontier(output, config=config)
    elapsed = max(time.monotonic() - started, 1.0e-9)

    manifest = summary["manifest"]
    integrity = manifest["integrity"]
    telemetry = manifest["telemetry"]
    assert summary["phase_one"]["interrupted"] is True
    assert summary["phase_two"]["resumed"] is True
    assert summary["exact_total_reached"] is True
    assert integrity["event_count"] == 2_000_000
    assert integrity["distinct_event_ids"] == 2_000_000
    assert integrity["duplicate_ids"] == 0
    assert integrity["orphan_parent_count"] == 0
    assert integrity["subject_count"] == 250_000
    assert integrity["complete_subject_count"] == 250_000
    assert integrity["m_minus_event_count"] == 250_000
    assert integrity["minimum_sequence"] == 0
    assert integrity["maximum_sequence"] == 1_999_999
    assert integrity["contiguous"] is True
    assert integrity["all_subjects_complete"] is True

    bytes_written = sum(path.stat().st_size for path in (output / "shards").glob("*.jsonl"))
    bytes_written += (output / "million-index.sqlite3").stat().st_size
    observation = FrontierObservation(
        plan_id=plan.plan_id,
        stage_index=1,
        attempted_events=2_000_000,
        accepted_events=2_000_000,
        elapsed_seconds=elapsed,
        bytes_written=bytes_written,
        peak_rss_bytes=int(telemetry["peak_rss_bytes"]),
        maximum_batch_latency_seconds=float(telemetry["last_batch_seconds"]),
        error_count=int(telemetry["rejected_events"]),
        duplicate_count=int(integrity["duplicate_ids"]),
        orphan_parent_count=int(integrity["orphan_parent_count"]),
        complete_subjects=int(integrity["complete_subject_count"]),
        interrupted_and_resumed=True,
        ledger_digest=str(integrity["ledger_digest"]),
    )
    decision = decide_next(plan, observation)
    assert decision.decision is Decision.EXPAND
    assert decision.next_target_events == 4_000_000
    assert decision.m_minus == ()

    ledger = ConductorLedger(tmp_path / "conductor-ledger")
    assert ledger.append(observation, decision) is True
    audit = ledger.audit()
    assert audit["status"] == "PASS"
    assert audit["entries"] == 1
    assert audit["m_minus_records"] == 0
