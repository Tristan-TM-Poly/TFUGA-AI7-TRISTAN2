from __future__ import annotations

import json

from omega_unbounded_t import (
    AdaptiveController,
    CapacityPolicy,
    ListWorkSource,
    MMinusLedger,
    SyntheticCapacityExecutor,
)


def test_controller_completes_large_finite_workload_without_permanent_cap(tmp_path):
    source = ListWorkSource(range(50_000))
    executor = SyntheticCapacityExecutor(capacity=128, redesign_factor=2.0)
    ledger = MMinusLedger(tmp_path / "m_minus.jsonl")
    controller = AdaptiveController(
        source,
        executor,
        initial_batch=64,
        ledger=ledger,
        checkpoint_path=tmp_path / "checkpoint.json",
    )

    report = controller.run()

    assert report.status == "completed"
    assert report.total_integrated == 50_000
    assert report.remaining == 0
    assert report.saturation_count >= 1
    assert report.redesign_count == report.saturation_count
    assert report.largest_safe_batch > 128
    assert executor.frontier_history[-1] > executor.frontier_history[0]
    assert ledger.events


def test_saturation_is_written_to_append_only_negative_memory(tmp_path):
    ledger_path = tmp_path / "m_minus.jsonl"
    controller = AdaptiveController(
        ListWorkSource(range(300)),
        SyntheticCapacityExecutor(capacity=32, allow_redesign=False),
        initial_batch=64,
        ledger=MMinusLedger(ledger_path),
    )

    report = controller.run()
    records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

    assert report.status == "paused_requires_redesign"
    assert report.total_integrated == 0
    assert report.remaining == 300
    assert len(records) == 1
    assert records[0]["requested_batch"] == 64
    assert "synthetic_capacity" in records[0]["limiting_dimensions"]


def test_empty_workload_completes_without_artificial_iteration():
    report = AdaptiveController(
        ListWorkSource([]),
        SyntheticCapacityExecutor(capacity=1),
    ).run()

    assert report.status == "completed"
    assert report.iterations == 0
    assert report.total_integrated == 0


def test_quality_gate_pauses_instead_of_accepting_low_quality_batch():
    executor = SyntheticCapacityExecutor(capacity=10_000, quality_score=0.7, allow_redesign=False)
    report = AdaptiveController(
        ListWorkSource(range(100)),
        executor,
        initial_batch=50,
        policy=CapacityPolicy(quality_floor=0.95),
    ).run()

    assert report.status == "paused_requires_redesign"
    assert report.total_integrated == 0
    assert report.remaining == 100
