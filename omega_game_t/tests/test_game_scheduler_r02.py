from __future__ import annotations

from omega_game.engines.scheduler import (
    CostGraph,
    DirtyFrontier,
    ScheduledEvent,
    SparseEventScheduler,
    SystemSpec,
    TemporalLODPolicy,
    TemporalSignal,
    run_sparse_benchmark,
)


def test_dirty_frontier_is_deduplicated_and_deterministic() -> None:
    frontier = DirtyFrontier()
    frontier.mark_many(["b", "a", "b", "c"])
    assert frontier.snapshot() == ("a", "b", "c")
    assert frontier.consume(2) == ("a", "b")
    assert frontier.snapshot() == ("c",)


def test_temporal_lod_policy_orders_cadences() -> None:
    policy = TemporalLODPolicy()
    assert policy.interval(TemporalSignal(visible=True)) == 1
    assert policy.interval(TemporalSignal(activity=1.0, importance=1.0)) == 1
    assert policy.interval(TemporalSignal(activity=0.5, importance=0.5)) == 2
    assert policy.interval(TemporalSignal(activity=0.2)) == 32
    assert policy.interval(TemporalSignal(activity=0.25, importance=0.1)) == 8
    assert policy.interval(TemporalSignal()) == 32


def test_sparse_scheduler_skips_idle_systems() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("physics"))
    report = scheduler.dispatch_tick(0)
    assert report.dispatches == ()
    assert report.skipped_systems == ("physics",)
    assert report.estimated_work == 0.0


def test_dirty_frontier_wakes_system_immediately() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("agents", max_batch=2))
    scheduler.mark_many("agents", ["e3", "e1", "e2"])
    first = scheduler.dispatch_tick(0)
    assert first.dispatches[0].entity_ids == ("e1", "e2")
    assert "dirty" in first.dispatches[0].reasons
    assert scheduler.pending_dirty("agents") == ("e3",)

    second = scheduler.dispatch_tick(1)
    assert second.dispatches[0].entity_ids == ("e3",)
    assert scheduler.pending_dirty("agents") == ()


def test_temporal_lod_can_delay_dirty_work_when_requested() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("economy", wake_on_dirty=False))
    scheduler.mark_dirty("economy", "city")
    first = scheduler.dispatch_tick(0, signals={"economy": TemporalSignal()})
    assert len(first.dispatches) == 1
    assert first.dispatches[0].interval == 32

    scheduler.mark_dirty("economy", "city")
    for tick in range(1, 32):
        report = scheduler.dispatch_tick(tick, signals={"economy": TemporalSignal()})
        assert report.dispatches == ()
    due = scheduler.dispatch_tick(32, signals={"economy": TemporalSignal()})
    assert len(due.dispatches) == 1


def test_event_wakes_dormant_system_and_marks_entity_dirty() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("quest", wake_on_dirty=False, wake_on_event=True))
    scheduler.dispatch_tick(0, signals={"quest": TemporalSignal()})
    scheduler.schedule_event(ScheduledEvent(3, "ev-1", "quest", entity_id="hero", payload={"kind": "arrival"}))
    assert scheduler.dispatch_tick(1).dispatches == ()
    assert scheduler.dispatch_tick(2).dispatches == ()
    report = scheduler.dispatch_tick(3)
    assert len(report.dispatches) == 1
    dispatch = report.dispatches[0]
    assert dispatch.entity_ids == ("hero",)
    assert dispatch.events[0].event_id == "ev-1"
    assert "event" in dispatch.reasons


def test_event_order_is_stable_for_same_tick() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("events"))
    scheduler.schedule_event(ScheduledEvent(2, "first", "events"))
    scheduler.schedule_event(ScheduledEvent(2, "second", "events"))
    report = scheduler.dispatch_tick(2)
    assert [event.event_id for event in report.dispatches[0].events] == ["first", "second"]


def test_priority_order_is_deterministic() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("low", priority=0))
    scheduler.register(SystemSpec("high", priority=10))
    scheduler.mark_dirty("low", "x")
    scheduler.mark_dirty("high", "y")
    report = scheduler.dispatch_tick(0)
    assert [dispatch.system_id for dispatch in report.dispatches] == ["high", "low"]


def test_cost_graph_accounts_work_units() -> None:
    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("agents", cost_per_entity=2.0, cost_per_event=0.5))
    scheduler.mark_many("agents", ["a", "b"])
    scheduler.schedule_event(ScheduledEvent(0, "spawn", "agents", entity_id="a"))
    report = scheduler.dispatch_tick(0)
    cost = CostGraph()
    cost.observe(report)
    assert report.estimated_work == 4.5
    assert cost.estimated_work == 4.5
    assert cost.nodes["agents"].processed_entities == 2
    assert cost.nodes["agents"].processed_events == 1


def test_sparse_benchmark_matches_accounting_identity() -> None:
    report = run_sparse_benchmark(entity_count=1000, active_entities=25, ticks=20, seed=7)
    assert report.naive_work_units == 20_000.0
    assert report.sparse_work_units == 500.0
    assert report.reduction_ratio == 0.975
    assert report.dispatch_count == 20


def test_sparse_benchmark_is_deterministic() -> None:
    a = run_sparse_benchmark(entity_count=500, active_entities=17, ticks=11, seed=99)
    b = run_sparse_benchmark(entity_count=500, active_entities=17, ticks=11, seed=99)
    assert a.to_json() == b.to_json()


def test_invalid_scheduler_contracts_fail_closed() -> None:
    scheduler = SparseEventScheduler()
    try:
        scheduler.register(SystemSpec("", max_batch=1))
    except ValueError:
        pass
    else:
        raise AssertionError("empty system_id should fail")

    scheduler.register(SystemSpec("ok"))
    try:
        scheduler.schedule_event(ScheduledEvent(-1, "bad", "ok"))
    except ValueError:
        pass
    else:
        raise AssertionError("negative event tick should fail")
