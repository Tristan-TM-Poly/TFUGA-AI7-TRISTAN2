from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

import pytest

from omega_discovery_kernel_t import (
    COMPACT_CORE_EVENT_TYPES,
    CompactMillionFrontier,
    MillionFrontierConfig,
    run_forced_resume_million_frontier,
)


def test_million_config_is_finite_calibration_without_permanent_cap() -> None:
    config = MillionFrontierConfig()
    assert config.validate() == []
    assert config.target_events == 1_000_000
    assert config.forced_interrupt_after == 524_288
    assert config.target_events % len(COMPACT_CORE_EVENT_TYPES) == 0
    assert config.forced_interrupt_after % len(COMPACT_CORE_EVENT_TYPES) == 0
    assert "max_total_events" not in asdict(config)


def test_million_config_rejects_partial_subject_boundaries() -> None:
    target = MillionFrontierConfig(target_events=1_000_001)
    assert any("divisible" in issue for issue in target.validate())
    interruption = MillionFrontierConfig(forced_interrupt_after=524_289)
    assert any("subject boundary" in issue for issue in interruption.validate())


def test_compact_records_are_deterministic_parented_and_tamper_evident(tmp_path: Path) -> None:
    config = MillionFrontierConfig(
        target_events=8_000,
        forced_interrupt_after=4_096,
        minimum_free_bytes=0,
    )
    with CompactMillionFrontier(tmp_path / "records", config=config) as frontier:
        first = frontier.make_record(0)
        same = frontier.make_record(0)
        second = frontier.make_record(1)
        eighth = frontier.make_record(7)
        ninth = frontier.make_record(8)

        assert first == same
        assert first.event_type == "ObservationEvent"
        assert second.parent_sequence == 0
        assert eighth.event_type == "ActionProposal"
        assert ninth.parent_sequence is None
        assert ninth.subject_index == 1
        assert first.event_hash != second.event_hash


def test_small_forced_interruption_resumes_without_duplicates(tmp_path: Path) -> None:
    config = MillionFrontierConfig(
        target_events=8_000,
        forced_interrupt_after=4_096,
        namespace_count=16,
        initial_shard_bytes=32_768,
        checkpoint_interval=512,
        sqlite_batch_size=256,
        minimum_free_bytes=0,
        latency_saturation_seconds_per_10k=60.0,
        rss_saturation_bytes=16 * 1024 * 1024 * 1024,
    )
    output = tmp_path / "small-million-frontier"
    summary = run_forced_resume_million_frontier(output, config=config)
    integrity = summary["manifest"]["integrity"]

    assert summary["phase_one"]["interrupted"] is True
    assert summary["phase_two"]["resumed"] is True
    assert summary["exact_total_reached"] is True
    assert integrity["event_count"] == 8_000
    assert integrity["distinct_event_ids"] == 8_000
    assert integrity["duplicate_ids"] == 0
    assert integrity["orphan_parent_count"] == 0
    assert integrity["subject_count"] == 1_000
    assert integrity["complete_subject_count"] == 1_000
    assert integrity["m_minus_event_count"] == 1_000
    assert integrity["contiguous"] is True
    assert integrity["all_subjects_complete"] is True

    saturation = [
        json.loads(line)
        for line in (output / "saturation-m-minus.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(item["kind"] == "forced_interruption" for item in saturation)

    checkpoint = json.loads((output / "million-checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["complete"] is True
    assert checkpoint["next_sequence"] == 8_000
    assert checkpoint["finite_target_is_not_permanent_ceiling"] is True

    with CompactMillionFrontier(output, config=config, resume=True) as resumed:
        assert resumed.run() == 0
        assert resumed.integrity_report()["event_count"] == 8_000


def test_one_million_event_forced_resume_frontier(tmp_path: Path) -> None:
    """Actual million-event OAKBench: disk-backed, interrupted, resumed, audited."""

    config = MillionFrontierConfig(
        target_events=1_000_000,
        forced_interrupt_after=524_288,
        namespace_count=256,
        initial_shard_bytes=4 * 1024 * 1024,
        shard_growth_factor=1.6,
        checkpoint_interval=50_000,
        sqlite_batch_size=10_000,
        minimum_free_bytes=256 * 1024 * 1024,
        latency_saturation_seconds_per_10k=60.0,
        rss_saturation_bytes=4 * 1024 * 1024 * 1024,
    )
    output = tmp_path / "frontier-1m-r0-3"
    summary = run_forced_resume_million_frontier(output, config=config)
    manifest = summary["manifest"]
    integrity = manifest["integrity"]

    assert summary["phase_one"]["interrupted"] is True
    assert summary["exact_total_reached"] is True
    assert manifest["checkpoint_complete"] is True
    assert manifest["next_sequence"] == 1_000_000
    assert manifest["remote_mutations"] == 0
    assert manifest["shard_count"] > 1
    assert manifest["saturation_record_count"] >= 1

    assert integrity["event_count"] == 1_000_000
    assert integrity["distinct_event_ids"] == 1_000_000
    assert integrity["duplicate_ids"] == 0
    assert integrity["orphan_parent_count"] == 0
    assert integrity["subject_count"] == 125_000
    assert integrity["complete_subject_count"] == 125_000
    assert integrity["m_minus_event_count"] == 125_000
    assert integrity["minimum_sequence"] == 0
    assert integrity["maximum_sequence"] == 999_999
    assert integrity["contiguous"] is True
    assert integrity["all_subjects_complete"] is True
    assert len(integrity["ledger_digest"]) == 64

    shard_files = sorted((output / "shards").glob("*.jsonl"))
    assert len(shard_files) == manifest["shard_count"]
    assert all(path.stat().st_size > 0 for path in shard_files)

    with sqlite3.connect(output / "million-index.sqlite3") as connection:
        event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        subject_count = connection.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        first = connection.execute(
            "SELECT sequence, event_code, parent_sequence FROM events ORDER BY sequence LIMIT 1"
        ).fetchone()
        last = connection.execute(
            "SELECT sequence, event_code, parent_sequence FROM events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
    assert event_count == 1_000_000
    assert subject_count == 125_000
    assert first == (0, 0, None)
    assert last == (999_999, 7, 999_998)

    saturation_lines = [
        json.loads(line)
        for line in (output / "saturation-m-minus.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    forced = [item for item in saturation_lines if item["kind"] == "forced_interruption"]
    assert len(forced) == 1
    assert forced[0]["event_count"] == 524_288
    assert "resume" in forced[0]["redesign_action"].lower()


@pytest.mark.parametrize("sequence", [0, 1, 7, 8, 999, 7_999])
def test_compact_event_hash_is_stable_across_instances(tmp_path: Path, sequence: int) -> None:
    config = MillionFrontierConfig(
        target_events=8_000,
        forced_interrupt_after=4_096,
        minimum_free_bytes=0,
    )
    with CompactMillionFrontier(tmp_path / f"first-{sequence}", config=config) as first:
        left = first.make_record(sequence)
    with CompactMillionFrontier(tmp_path / f"second-{sequence}", config=config) as second:
        right = second.make_record(sequence)
    assert left == right
