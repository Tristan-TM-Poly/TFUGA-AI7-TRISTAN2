import pytest

from omega_re_t.campaign_orchestrator_r05 import (
    ResourceEnvelope,
    merge_shard_results,
    plan_shards,
    run_campaign,
)


def generator(index):
    return {"index": index}


def evaluator(item):
    return item["index"] % 3 != 2, {"value": item["index"] * 2}, 1.0


def test_shard_plan_is_contiguous_and_balanced():
    shards = plan_shards(start_index=10, count=10, shard_count=3)
    assert shards == ((10, 4), (14, 3), (17, 3))


def test_campaign_has_no_permanent_cap_and_is_deterministic():
    envelope = ResourceEnvelope(5, 10.0, 5)
    _, first = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=evaluator)
    _, second = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=evaluator)
    assert first == second
    assert first.permanent_total_cap is None
    assert first.evaluated_count == 5
    assert first.next_index == 5


def test_campaign_stops_on_cost_before_overrun():
    envelope = ResourceEnvelope(10, 2.5, 10)
    results, checkpoint = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=evaluator)
    assert len(results) == 2
    assert checkpoint.consumed_cost_units == 2.0


def test_campaign_stops_after_failure_budget_exceeded():
    envelope = ResourceEnvelope(10, 100.0, 0)
    results, checkpoint = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=lambda item: (False, {}, 1.0))
    assert len(results) == 1
    assert checkpoint.failed_count == 1


def test_evaluator_exception_is_recorded():
    envelope = ResourceEnvelope(2, 10.0, 2)
    results, checkpoint = run_campaign(
        start_index=0,
        envelope=envelope,
        generator=generator,
        evaluator=lambda item: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert results[0].error == "RuntimeError:boom"
    assert checkpoint.failed_count == 2


def test_merge_shards_rejects_overlap_and_gap():
    envelope = ResourceEnvelope(2, 10.0, 2)
    left = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=evaluator)
    right_overlap = run_campaign(start_index=1, envelope=envelope, generator=generator, evaluator=evaluator)
    with pytest.raises(ValueError, match="overlapping"):
        merge_shard_results((left, right_overlap))
    right_gap = run_campaign(start_index=3, envelope=envelope, generator=generator, evaluator=evaluator)
    with pytest.raises(ValueError, match="gap"):
        merge_shard_results((left, right_gap))


def test_merge_shards_accepts_contiguous_results():
    envelope = ResourceEnvelope(2, 10.0, 2)
    left = run_campaign(start_index=0, envelope=envelope, generator=generator, evaluator=evaluator)
    right = run_campaign(start_index=2, envelope=envelope, generator=generator, evaluator=evaluator)
    merged = merge_shard_results((right, left))
    assert [item.index for item in merged] == [0, 1, 2, 3]
