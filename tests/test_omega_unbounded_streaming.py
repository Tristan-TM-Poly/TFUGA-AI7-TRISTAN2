from __future__ import annotations

import json

from omega_unbounded_t import MPlusLedger, RangeWorkSource, ResourceSampler


def test_range_work_source_is_lazy_replayable_and_restorable():
    source = RangeWorkSource(1_000_000)

    first = source.take(3)
    assert first == [0, 1, 2]
    assert source.remaining == 999_997

    source.requeue_front(first)
    assert source.remaining == 1_000_000
    assert source.take(5) == [0, 1, 2, 3, 4]

    restored = RangeWorkSource.restore(source.checkpoint())
    assert restored.remaining == source.remaining
    assert restored.take(4) == source.take(4)


def test_m_plus_ledger_requires_a_real_frontier_gain(tmp_path):
    ledger_path = tmp_path / "m_plus.jsonl"
    ledger = MPlusLedger(ledger_path)
    event = ledger.record(
        previous_frontier=1_024,
        new_frontier=4_096,
        intervention=("disk_backed_index", "adaptive_shards"),
        repetitions=3,
        quality_before=0.96,
        quality_after=0.97,
        status="reproduced_candidate_for_canon",
    )

    record = json.loads(ledger_path.read_text(encoding="utf-8").strip())
    assert event.gain == 4.0
    assert record["gain"] == 4.0
    assert record["new_frontier"] == 4_096
    assert record["repetitions"] == 3


def test_resource_sampler_returns_disk_and_process_observations(tmp_path):
    snapshot = ResourceSampler(tmp_path).sample()

    assert snapshot.disk_total_bytes > 0
    assert snapshot.disk_free_bytes >= 0
    assert snapshot.process_cpu_seconds >= 0
    assert snapshot.monotonic_seconds > 0
