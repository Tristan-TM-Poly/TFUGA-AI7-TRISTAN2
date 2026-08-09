from __future__ import annotations

from dataclasses import replace

from omega_game.engines.campaign import plan_campaign
from omega_game.engines.campaign_bundle import WorkerManifest
from omega_game.engines.campaign_coordinator import (
    CampaignCoordinator,
    CoordinatorLedger,
    replay_coordinator_events,
)
from omega_game.engines.evolution import seed_population
from omega_game.engines.simulation import ArenaConfig


class FakeClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = float(value)

    def __call__(self) -> float:
        return self.value

    def advance(self, amount: float) -> None:
        self.value += float(amount)


def _manifest():
    return plan_campaign(
        seed_population(3, seed=1201),
        seeds=(1,),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=2,
        mirrored=True,
    )


def _successful_coordinator(clock_value: float = 0.0):
    clock = FakeClock(clock_value)
    coordinator = CampaignCoordinator(_manifest(), max_attempts=2, clock=clock)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a", lease_ttl_seconds=10, heartbeat_ttl_seconds=10)
    coordinator.acknowledge(shard_id, "worker-a")
    coordinator.succeed(shard_id, "worker-a", "checkpoint-abc")
    return coordinator, clock, shard_id


def test_successful_lifecycle_has_valid_chain_and_replay() -> None:
    coordinator, _, shard_id = _successful_coordinator()
    coordinator.ledger.validate_chain()
    audit = coordinator.audit()
    assert audit.accepted
    assert coordinator.shard_states[shard_id].status == "succeeded"
    replayed = replay_coordinator_events(
        coordinator.manifest,
        coordinator.ledger.events,
        max_attempts=coordinator.max_attempts,
    )
    assert replayed[shard_id].to_dict() == coordinator.shard_states[shard_id].to_dict()


def test_logical_event_chain_is_independent_of_clock_origin() -> None:
    first, _, _ = _successful_coordinator(10)
    second, _, _ = _successful_coordinator(1000)
    assert [event.event_receipt for event in first.ledger.events] == [
        event.event_receipt for event in second.ledger.events
    ]
    assert first.ledger.head_receipt == second.ledger.head_receipt


def test_illegal_duplicate_ack_does_not_append_event() -> None:
    clock = FakeClock()
    coordinator = CampaignCoordinator(_manifest(), clock=clock)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    coordinator.acknowledge(shard_id, "worker-a")
    count = len(coordinator.ledger.events)
    try:
        coordinator.acknowledge(shard_id, "worker-a")
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate acknowledgement should fail")
    assert len(coordinator.ledger.events) == count


def test_wrong_worker_cannot_ack_or_complete_shard() -> None:
    coordinator = CampaignCoordinator(_manifest())
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.register_worker(WorkerManifest("worker-b"))
    coordinator.heartbeat("worker-a")
    coordinator.heartbeat("worker-b")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    for action in (
        lambda: coordinator.acknowledge(shard_id, "worker-b"),
        lambda: coordinator.succeed(shard_id, "worker-b", "checkpoint"),
    ):
        count = len(coordinator.ledger.events)
        try:
            action()
        except ValueError:
            pass
        else:
            raise AssertionError("non-owner transition should fail")
        assert len(coordinator.ledger.events) == count


def test_failure_at_attempt_limit_exhausts_shard_and_replays() -> None:
    coordinator = CampaignCoordinator(_manifest(), max_attempts=1)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    coordinator.acknowledge(shard_id, "worker-a")
    events = coordinator.fail(shard_id, "worker-a", "failure-receipt")
    assert len(events) == 1
    assert coordinator.shard_states[shard_id].status == "exhausted"
    assert coordinator.audit().accepted


def test_lease_expiry_at_attempt_limit_exhausts_shard() -> None:
    clock = FakeClock(0)
    coordinator = CampaignCoordinator(_manifest(), max_attempts=1, clock=clock)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a", lease_ttl_seconds=2, heartbeat_ttl_seconds=10)
    clock.advance(2)
    events = coordinator.expire_leases()
    assert events and events[0].kind == "lease_expired"
    assert coordinator.shard_states[shard_id].status == "exhausted"
    assert coordinator.audit().accepted


def test_failure_schedules_retry_and_next_assignment_increments_attempt() -> None:
    coordinator = CampaignCoordinator(_manifest(), max_attempts=2)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = coordinator.manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    coordinator.fail(shard_id, "worker-a", "failure-1")
    assert coordinator.shard_states[shard_id].status == "retry_pending"
    assert coordinator.ledger.events[-1].kind == "retry_scheduled"
    coordinator.heartbeat("worker-a")
    assigned = coordinator.assign(shard_id, "worker-a")
    assert assigned.attempt == 2
    assert coordinator.shard_states[shard_id].attempt == 2


def test_tampering_old_event_breaks_chain() -> None:
    coordinator, _, _ = _successful_coordinator()
    events = list(coordinator.ledger.events)
    events[1] = replace(events[1], payload={"tampered": True})
    ledger = CoordinatorLedger(coordinator.manifest.plan_receipt, events=events)
    try:
        ledger.validate_chain()
    except ValueError:
        pass
    else:
        raise AssertionError("tampered event should break receipt validation")


def test_reordered_or_missing_event_breaks_causal_validation() -> None:
    coordinator, _, _ = _successful_coordinator()
    for events in (
        list(reversed(coordinator.ledger.events)),
        coordinator.ledger.events[1:],
    ):
        ledger = CoordinatorLedger(coordinator.manifest.plan_receipt, events=list(events))
        try:
            ledger.validate_chain()
        except ValueError:
            pass
        else:
            raise AssertionError("reordered/missing events should fail")


def test_summary_counts_terminal_shards() -> None:
    coordinator, _, shard_id = _successful_coordinator()
    summary = coordinator.summary()
    assert summary["successful_shards"] == 1
    assert summary["exhausted_shards"] == 0
    assert not summary["terminal"]  # another shard remains pending
    assert summary["shard_states"][shard_id]["status"] == "succeeded"
