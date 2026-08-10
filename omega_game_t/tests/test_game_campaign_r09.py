from __future__ import annotations

from dataclasses import replace

from omega_game.engines.campaign import (
    CampaignCheckpoint,
    benchmark_campaign,
    merge_checkpoints,
    plan_campaign,
    run_campaign_slice,
)
from omega_game.engines.evolution import seed_population
from omega_game.engines.layout import ArenaLayout
from omega_game.engines.simulation import ArenaConfig


def _layout() -> ArenaLayout:
    return ArenaLayout(
        width=5,
        height=3,
        left_spawn=(0, 1),
        right_spawn=(4, 1),
        resources=((1, 0), (1, 2), (3, 0), (3, 2)),
        obstacles=(),
    )


def test_campaign_job_cardinality_and_plan_are_deterministic() -> None:
    agents = seed_population(3, seed=1)
    kwargs = {
        "layouts": (_layout(),),
        "seeds": (2, 3),
        "arena_template": ArenaConfig(max_steps=5),
        "mirrored": True,
        "shard_count": 3,
    }
    a = plan_campaign(agents, **kwargs)
    b = plan_campaign(tuple(reversed(agents)), **kwargs)
    # C(3,2) * 2 seeds * 2 orientations * 1 layout
    assert a.job_count == 12
    assert a.to_json() == b.to_json()
    assert a.plan_receipt == b.plan_receipt


def test_shards_partition_jobs_exactly_once() -> None:
    manifest = plan_campaign(seed_population(4, seed=2), seeds=(1,), shard_count=5, arena_template=ArenaConfig(max_steps=4))
    flat = [job_id for shard in manifest.shards for job_id in shard.job_ids]
    assert len(flat) == manifest.job_count
    assert len(set(flat)) == manifest.job_count
    assert set(flat) == {job.job_id for job in manifest.jobs}
    manifest.validate()


def test_backpressure_and_resume_do_not_reexecute_completed_jobs() -> None:
    manifest = plan_campaign(seed_population(3, seed=3), seeds=(1, 2), shard_count=2, arena_template=ArenaConfig(max_steps=4))
    checkpoint, first = run_campaign_slice(manifest, max_jobs=3)
    assert len(first.executed_job_ids) == 3
    assert first.total_completed_jobs == 3
    assert not first.complete_campaign
    first_receipts = {job_id: checkpoint.completed[job_id].result_receipt for job_id in checkpoint.completed}

    checkpoint, second = run_campaign_slice(manifest, checkpoint=checkpoint, max_jobs=3)
    assert set(first.executed_job_ids).isdisjoint(second.executed_job_ids)
    assert set(first.executed_job_ids).issubset(second.skipped_completed_job_ids)
    for job_id, receipt in first_receipts.items():
        assert checkpoint.completed[job_id].result_receipt == receipt

    while len(checkpoint.completed) < manifest.job_count:
        checkpoint, _ = run_campaign_slice(manifest, checkpoint=checkpoint, max_jobs=3)
    assert len(checkpoint.completed) == manifest.job_count
    final_checkpoint, final_report = run_campaign_slice(manifest, checkpoint=checkpoint)
    assert final_report.executed_job_ids == ()
    assert final_report.complete_campaign
    assert final_checkpoint.checkpoint_receipt == checkpoint.checkpoint_receipt


def test_shards_can_execute_independently_then_merge() -> None:
    manifest = plan_campaign(seed_population(3, seed=4), seeds=(7,), shard_count=3, arena_template=ArenaConfig(max_steps=4))
    pieces = []
    for shard in manifest.shards:
        checkpoint, report = run_campaign_slice(manifest, shard_ids=(shard.shard_id,))
        assert report.selected_shards == (shard.shard_id,)
        pieces.append(checkpoint)
    merged = merge_checkpoints(manifest, pieces)
    assert len(merged.completed) == manifest.job_count

    sequential, report = run_campaign_slice(manifest)
    assert report.complete_campaign
    assert merged.checkpoint_receipt == sequential.checkpoint_receipt


def test_layout_campaign_propagates_layout_hash() -> None:
    layout = _layout()
    manifest = plan_campaign(
        seed_population(2, seed=5),
        layouts=(layout,),
        seeds=(9,),
        arena_template=ArenaConfig(max_steps=4),
        shard_count=1,
    )
    checkpoint, report = run_campaign_slice(manifest)
    assert report.complete_campaign
    assert checkpoint.completed
    assert {result.layout_hash for result in checkpoint.completed.values()} == {layout.layout_hash}


def test_checkpoint_plan_mismatch_fails_closed() -> None:
    agents = seed_population(3, seed=6)
    first = plan_campaign(agents, seeds=(1,), arena_template=ArenaConfig(max_steps=4))
    second = plan_campaign(agents, seeds=(2,), arena_template=ArenaConfig(max_steps=4))
    checkpoint, _ = run_campaign_slice(first, max_jobs=1)
    try:
        run_campaign_slice(second, checkpoint=checkpoint)
    except ValueError:
        pass
    else:
        raise AssertionError("foreign checkpoint should fail")


def test_tampered_result_receipt_fails_closed() -> None:
    manifest = plan_campaign(seed_population(2, seed=7), seeds=(1,), arena_template=ArenaConfig(max_steps=4))
    checkpoint, _ = run_campaign_slice(manifest)
    job_id = next(iter(checkpoint.completed))
    checkpoint.completed[job_id] = replace(checkpoint.completed[job_id], result_receipt="0" * 64)
    try:
        checkpoint.validate_for(manifest)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered result receipt should fail")


def test_invalid_shard_and_zero_backpressure_fail_closed() -> None:
    manifest = plan_campaign(seed_population(2, seed=8), seeds=(1,), arena_template=ArenaConfig(max_steps=4))
    for kwargs in ({"shard_ids": (99,)}, {"max_jobs": 0}):
        try:
            run_campaign_slice(manifest, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid slice arguments should fail: {kwargs}")


def test_benchmark_separates_deterministic_work_from_wall_clock() -> None:
    manifest = plan_campaign(seed_population(2, seed=9), seeds=(1,), arena_template=ArenaConfig(max_steps=4))
    benchmark = benchmark_campaign(manifest, repetitions=2)
    assert benchmark.repetitions == 2
    assert benchmark.job_count == manifest.job_count
    assert len(set(benchmark.deterministic_ticks_per_run)) == 1
    assert len(set(benchmark.deterministic_events_per_run)) == 1
    assert all(value >= 0 for value in benchmark.wall_clock_seconds_per_run)
    assert benchmark.median_wall_clock_seconds >= 0
    assert benchmark.result_receipt
