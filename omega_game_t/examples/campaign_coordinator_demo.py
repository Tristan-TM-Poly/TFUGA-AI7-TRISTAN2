from __future__ import annotations

import json

from omega_game.engines.campaign import plan_campaign
from omega_game.engines.campaign_bundle import WorkerManifest
from omega_game.engines.campaign_coordinator import CampaignCoordinator
from omega_game.engines.evolution import seed_population
from omega_game.engines.simulation import ArenaConfig


def main() -> int:
    manifest = plan_campaign(
        seed_population(3, seed=1201),
        seeds=(1,),
        arena_template=ArenaConfig(max_steps=4, resource_count=2),
        shard_count=2,
    )
    coordinator = CampaignCoordinator(manifest, max_attempts=1)
    coordinator.register_worker(WorkerManifest("worker-a", tags=("local",)))
    coordinator.register_worker(WorkerManifest("worker-b", tags=("local",)))
    coordinator.heartbeat("worker-a")
    coordinator.heartbeat("worker-b")

    first = manifest.shards[0].shard_id
    second = manifest.shards[1].shard_id

    coordinator.assign(first, "worker-a")
    coordinator.acknowledge(first, "worker-a")
    coordinator.succeed(first, "worker-a", "checkpoint-shard-a")

    coordinator.assign(second, "worker-b")
    coordinator.acknowledge(second, "worker-b")
    coordinator.fail(second, "worker-b", "failure-shard-b")

    audit = coordinator.audit()
    if not audit.accepted:
        raise SystemExit(f"coordinator audit failed: {audit.flags}")

    print(
        json.dumps(
            {
                "ledger": coordinator.ledger.to_dict(),
                "summary": coordinator.summary(),
                "audit": audit.to_dict(),
                "boundaries": [
                    "event receipt proves internal causal integrity, not external event truth",
                    "controller ledger is not distributed consensus",
                    "lease expiry/failure state is orchestration evidence, not proof of worker death"
                ]
            },
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
