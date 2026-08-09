from __future__ import annotations

import json
from pathlib import Path

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_runtime import (
    CheckpointArtifact,
    LeaseLedger,
    ShardFailureReceipt,
    compare_process_execution,
    load_checkpoint,
    run_process_shards,
    save_checkpoint,
)
from omega_game.engines.evolution import seed_population
from omega_game.engines.simulation import ArenaConfig


def _manifest(shards: int = 2):
    return plan_campaign(
        seed_population(3, seed=101),
        seeds=(1,),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=shards,
        mirrored=True,
    )


def test_checkpoint_artifact_persistence_roundtrip_is_content_stable(tmp_path: Path) -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=2)
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_receipt = save_checkpoint(first_path, checkpoint)
    second_receipt = save_checkpoint(second_path, checkpoint)
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_receipt == second_receipt

    loaded, load_receipt = load_checkpoint(first_path, manifest)
    assert loaded.checkpoint_receipt == checkpoint.checkpoint_receipt
    assert load_receipt.content_sha256 == first_receipt.content_sha256
    assert load_receipt.byte_count == first_receipt.byte_count


def test_checkpoint_artifact_json_roundtrip() -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=1)
    artifact = CheckpointArtifact.from_checkpoint(checkpoint)
    text = json.dumps(artifact.to_dict(), sort_keys=True)
    restored = CheckpointArtifact.from_json(text).to_checkpoint(manifest)
    assert restored.checkpoint_receipt == checkpoint.checkpoint_receipt


def test_checkpoint_disk_tamper_fails_closed(tmp_path: Path) -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=1)
    path = tmp_path / "checkpoint.json"
    save_checkpoint(path, checkpoint)
    payload = json.loads(path.read_text())
    job_id = next(iter(payload["completed"]))
    payload["completed"][job_id]["left_score"] += 999
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        load_checkpoint(path, manifest)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered checkpoint artifact should fail")


def test_checkpoint_from_foreign_plan_fails_closed(tmp_path: Path) -> None:
    first = _manifest()
    second = plan_campaign(
        seed_population(3, seed=101),
        seeds=(2,),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=2,
    )
    checkpoint, _ = run_campaign_slice(first, max_jobs=1)
    path = tmp_path / "checkpoint.json"
    save_checkpoint(path, checkpoint)
    try:
        load_checkpoint(path, second)
    except ValueError:
        pass
    else:
        raise AssertionError("checkpoint from a different plan should fail")


def test_lease_ledger_prevents_double_assignment() -> None:
    ledger = LeaseLedger(plan_receipt="plan")
    lease = ledger.acquire(1, "worker-a", 1)
    try:
        ledger.acquire(1, "worker-b", 1)
    except ValueError:
        pass
    else:
        raise AssertionError("double lease should fail")
    ledger.release(lease)
    second = ledger.acquire(1, "worker-b", 2)
    assert second.lease_token != lease.lease_token
    ledger.release(second)
    assert ledger.active == {}
    assert ledger.released_tokens == [lease.lease_token, second.lease_token]


def test_failure_receipt_is_deterministic_without_raw_message() -> None:
    error = RuntimeError("synthetic secret-like error text")
    a = ShardFailureReceipt.from_exception(shard_id=2, attempt=1, worker_id="w", error=error)
    b = ShardFailureReceipt.from_exception(shard_id=2, attempt=1, worker_id="w", error=error)
    assert a == b
    assert "synthetic" not in json.dumps(a.to_dict())
    assert len(a.error_message_sha256) == 64
    assert len(a.failure_receipt) == 64


def test_single_worker_process_runtime_matches_campaign_completion() -> None:
    manifest = _manifest(shards=3)
    checkpoint, report = run_process_shards(manifest, workers=1)
    assert report.complete_campaign
    assert report.failed_shards == ()
    assert len(checkpoint.completed) == manifest.job_count


def test_multi_process_runtime_matches_single_worker_receipt() -> None:
    manifest = _manifest(shards=2)
    sequential, seq_report = run_process_shards(manifest, workers=1)
    parallel, par_report = run_process_shards(manifest, workers=2)
    assert seq_report.complete_campaign and par_report.complete_campaign
    assert sequential.checkpoint_receipt == parallel.checkpoint_receipt
    assert par_report.failed_shards == ()


def test_process_comparison_reports_empirical_not_asserted_speedup() -> None:
    manifest = _manifest(shards=2)
    report = compare_process_execution(manifest, workers=2)
    assert report.deterministic_equivalence
    assert report.sequential_checkpoint_receipt == report.process_checkpoint_receipt
    assert report.sequential_wall_clock_seconds >= 0
    assert report.process_wall_clock_seconds >= 0
    if report.observed_speedup is not None:
        assert report.observed_speedup >= 0


def test_process_runtime_rejects_invalid_controls() -> None:
    manifest = _manifest()
    for kwargs in ({"workers": 0}, {"max_attempts": 0}, {"shard_ids": (99,)}):
        try:
            run_process_shards(manifest, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid runtime controls should fail: {kwargs}")
