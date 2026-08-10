from __future__ import annotations

import json

from omega_game.engines.campaign import CampaignCheckpoint, plan_campaign, run_campaign_slice
from omega_game.engines.campaign_bundle import WorkerManifest
from omega_game.engines.campaign_coordinator import CampaignCoordinator, replay_coordinator_events
from omega_game.engines.evolution import seed_population
from omega_game.engines.simulation import ArenaConfig


def _manifest():
    return plan_campaign(
        seed_population(3, seed=1501),
        seeds=(1,),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=2,
        mirrored=True,
    )


def test_campaign_checkpoint_to_json_from_json_roundtrip_preserves_receipt() -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=2)
    restored = CampaignCheckpoint.from_json(checkpoint.to_json())
    assert restored.to_dict() == checkpoint.to_dict()
    assert restored.checkpoint_receipt == checkpoint.checkpoint_receipt
    restored.validate_for(manifest)


def test_campaign_checkpoint_serialized_receipt_tamper_fails_closed() -> None:
    manifest = _manifest()
    checkpoint, _ = run_campaign_slice(manifest, max_jobs=1)
    payload = json.loads(checkpoint.to_json())
    payload["checkpoint_receipt"] = "0" * 64
    try:
        CampaignCheckpoint.from_dict(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered serialized checkpoint receipt should fail")


def test_coordinator_retry_reassign_success_live_state_matches_replay() -> None:
    manifest = _manifest()
    coordinator = CampaignCoordinator(manifest, max_attempts=2)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = manifest.shards[0].shard_id

    coordinator.assign(shard_id, "worker-a")
    coordinator.acknowledge(shard_id, "worker-a")
    coordinator.fail(shard_id, "worker-a", "failure-attempt-1")
    assert coordinator.shard_states[shard_id].status == "retry_pending"
    assert coordinator.shard_states[shard_id].failure_receipt == "failure-attempt-1"

    coordinator.heartbeat("worker-a")
    coordinator.assign(shard_id, "worker-a")
    assert coordinator.shard_states[shard_id].attempt == 2
    assert coordinator.shard_states[shard_id].failure_receipt is None
    coordinator.acknowledge(shard_id, "worker-a")
    coordinator.succeed(shard_id, "worker-a", "checkpoint-attempt-2")

    replayed = replay_coordinator_events(
        manifest,
        coordinator.ledger.events,
        max_attempts=2,
    )
    assert replayed[shard_id].to_dict() == coordinator.shard_states[shard_id].to_dict()
    assert replayed[shard_id].failure_receipt is None
    assert coordinator.audit().accepted
