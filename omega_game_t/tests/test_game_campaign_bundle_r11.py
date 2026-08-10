from __future__ import annotations

import json
from pathlib import Path

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_bundle import (
    ArtifactReceipt,
    CampaignBundle,
    LocalContentAddressedStore,
    TTLLeaseCoordinator,
    WorkerManifest,
    WorkerRegistry,
    get_bundle,
    put_bundle,
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
        seed_population(3, seed=1101),
        seeds=(1, 2),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=3,
        mirrored=True,
    )


def test_worker_manifest_receipt_is_canonical() -> None:
    a = WorkerManifest("worker-a", max_concurrent_shards=2, tags=("cpu", "local"))
    b = WorkerManifest("worker-a", max_concurrent_shards=2, tags=("local", "cpu"))
    assert a.normalized_dict() == b.normalized_dict()
    assert a.manifest_receipt == b.manifest_receipt


def test_heartbeat_receipt_excludes_observation_time() -> None:
    manifest = WorkerManifest("worker-a")
    first_clock = FakeClock(10)
    second_clock = FakeClock(1000)
    first = WorkerRegistry(clock=first_clock)
    second = WorkerRegistry(clock=second_clock)
    first.register(manifest)
    second.register(manifest)
    a = first.heartbeat("worker-a")
    b = second.heartbeat("worker-a")
    assert a.observed_at != b.observed_at
    assert a.heartbeat_receipt == b.heartbeat_receipt


def test_worker_registry_active_and_stale_with_injected_clock() -> None:
    clock = FakeClock(0)
    registry = WorkerRegistry(clock=clock)
    registry.register(WorkerManifest("a"))
    registry.register(WorkerManifest("b"))
    registry.heartbeat("a")
    assert registry.active_workers(ttl_seconds=5) == ("a",)
    clock.advance(4)
    registry.heartbeat("b")
    assert registry.active_workers(ttl_seconds=5) == ("a", "b")
    clock.advance(2)
    assert registry.active_workers(ttl_seconds=5) == ("b",)


def test_ttl_lease_expires_and_can_be_reassigned() -> None:
    clock = FakeClock(0)
    registry = WorkerRegistry(clock=clock)
    registry.register(WorkerManifest("a"))
    registry.register(WorkerManifest("b"))
    registry.heartbeat("a")
    registry.heartbeat("b")
    coordinator = TTLLeaseCoordinator(plan_receipt="plan", registry=registry, clock=clock)
    first = coordinator.acquire(2, "a", lease_ttl_seconds=5, heartbeat_ttl_seconds=10)
    try:
        coordinator.acquire(2, "b", lease_ttl_seconds=5, heartbeat_ttl_seconds=10)
    except ValueError:
        pass
    else:
        raise AssertionError("unexpired shard lease should block reassignment")
    clock.advance(5)
    expired = coordinator.expire()
    assert expired == (first,)
    second = coordinator.acquire(2, "b", lease_ttl_seconds=5, heartbeat_ttl_seconds=10)
    assert second.epoch == first.epoch + 1
    assert second.lease_token != first.lease_token


def test_ttl_lease_requires_active_heartbeat_and_renewal() -> None:
    clock = FakeClock(0)
    registry = WorkerRegistry(clock=clock)
    registry.register(WorkerManifest("a"))
    coordinator = TTLLeaseCoordinator(plan_receipt="plan", registry=registry, clock=clock)
    try:
        coordinator.acquire(0, "a", lease_ttl_seconds=5, heartbeat_ttl_seconds=2)
    except ValueError:
        pass
    else:
        raise AssertionError("worker without heartbeat should not lease")
    registry.heartbeat("a")
    lease = coordinator.acquire(0, "a", lease_ttl_seconds=5, heartbeat_ttl_seconds=2)
    clock.advance(1)
    registry.heartbeat("a")
    renewed = coordinator.renew(lease, lease_ttl_seconds=5, heartbeat_ttl_seconds=2)
    assert renewed.lease_token == lease.lease_token
    assert renewed.expires_at > lease.expires_at
    coordinator.release(renewed)
    assert coordinator.active == {}


def test_local_cas_is_content_addressed_and_detects_corruption(tmp_path: Path) -> None:
    store = LocalContentAddressedStore(tmp_path / "cas")
    data = b"same-content\n"
    first = store.put_bytes(data, media_type="text/plain")
    second = store.put_bytes(data, media_type="text/plain")
    assert first == second
    assert store.get_bytes(first) == data
    path = store.path_for(first)
    path.write_bytes(b"tampered")
    try:
        store.get_bytes(first)
    except ValueError:
        pass
    else:
        raise AssertionError("corrupted CAS bytes should fail")


def test_campaign_bundle_roundtrip_restores_manifest_checkpoint_workers() -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=3)
    workers = (WorkerManifest("b", tags=("cpu",)), WorkerManifest("a", max_concurrent_shards=2))
    bundle = CampaignBundle.from_state(manifest, checkpoint=checkpoint, workers=workers)
    restored = CampaignBundle.from_json(bundle.to_json())
    manifest2, checkpoint2, workers2 = restored.restore()
    assert manifest2.plan_receipt == manifest.plan_receipt
    assert manifest2.to_json() == manifest.to_json()
    assert checkpoint2 is not None
    assert checkpoint2.checkpoint_receipt == checkpoint.checkpoint_receipt
    assert [worker.worker_id for worker in workers2] == ["a", "b"]
    assert restored.bundle_receipt == bundle.bundle_receipt


def test_bundle_restore_then_resume_matches_direct_campaign() -> None:
    manifest = _manifest()
    partial, _ = run_campaign_slice(manifest, max_jobs=2)
    bundle = CampaignBundle.from_state(manifest, checkpoint=partial)
    restored_manifest, restored_checkpoint, _ = bundle.restore()
    assert restored_checkpoint is not None
    resumed, _ = run_campaign_slice(restored_manifest, checkpoint=restored_checkpoint)
    direct, _ = run_campaign_slice(manifest)
    assert resumed.checkpoint_receipt == direct.checkpoint_receipt


def test_bundle_tamper_fails_closed() -> None:
    bundle = CampaignBundle.from_state(_manifest())
    payload = bundle.to_dict()
    payload["manifest"]["seeds"] = [999]
    try:
        CampaignBundle.from_dict(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered bundle should fail receipt validation")


def test_bundle_can_roundtrip_through_artifact_store(tmp_path: Path) -> None:
    bundle = CampaignBundle.from_state(_manifest(), workers=(WorkerManifest("worker-a"),))
    store = LocalContentAddressedStore(tmp_path / "store")
    receipt = put_bundle(store, bundle)
    assert receipt.media_type == "application/vnd.omega-game-campaign-bundle+json"
    restored = get_bundle(store, receipt)
    assert restored.bundle_receipt == bundle.bundle_receipt
    assert restored.to_json() == bundle.to_json()


def test_worker_manifest_protocol_and_duplicate_bundle_workers_fail_closed() -> None:
    try:
        WorkerManifest("a", protocol_version="9.9").validate()
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported worker protocol should fail")

    worker = WorkerManifest("same")
    try:
        CampaignBundle.from_state(_manifest(), workers=(worker, worker))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate worker IDs should fail")
