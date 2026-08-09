from __future__ import annotations

import json
import tempfile

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_bundle import (
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


def main() -> int:
    manifest = plan_campaign(
        seed_population(3, seed=1111),
        seeds=(1, 2),
        arena_template=ArenaConfig(max_steps=6, resource_count=3),
        shard_count=3,
    )
    checkpoint, first_slice = run_campaign_slice(manifest, max_jobs=3)
    workers = (WorkerManifest("worker-a", max_concurrent_shards=2, tags=("local", "cpu")),)
    bundle = CampaignBundle.from_state(manifest, checkpoint=checkpoint, workers=workers)

    with tempfile.TemporaryDirectory(prefix="omega-r11-") as root:
        store = LocalContentAddressedStore(root)
        artifact_receipt = put_bundle(store, bundle)
        restored_bundle = get_bundle(store, artifact_receipt)
        restored_manifest, restored_checkpoint, restored_workers = restored_bundle.restore()
        if restored_checkpoint is None:
            raise SystemExit("checkpoint missing after restore")

        registry = WorkerRegistry()
        registry.register(restored_workers[0])
        heartbeat = registry.heartbeat(restored_workers[0].worker_id)
        coordinator = TTLLeaseCoordinator(restored_manifest.plan_receipt, registry)
        lease = coordinator.acquire(
            restored_manifest.shards[0].shard_id,
            restored_workers[0].worker_id,
            lease_ttl_seconds=30,
            heartbeat_ttl_seconds=30,
        )
        coordinator.release(lease)

        completed, final_slice = run_campaign_slice(restored_manifest, checkpoint=restored_checkpoint)
        direct, _ = run_campaign_slice(manifest)
        if completed.checkpoint_receipt != direct.checkpoint_receipt:
            raise SystemExit("bundle-resumed checkpoint differs from direct execution")

        print(
            json.dumps(
                {
                    "bundle_receipt": bundle.bundle_receipt,
                    "artifact_receipt": artifact_receipt.to_dict(),
                    "plan_receipt": restored_manifest.plan_receipt,
                    "first_slice": first_slice.to_dict(),
                    "final_slice": final_slice.to_dict(),
                    "final_checkpoint_receipt": completed.checkpoint_receipt,
                    "worker_manifest_receipt": restored_workers[0].manifest_receipt,
                    "heartbeat": heartbeat.to_dict(),
                    "lease": lease.to_dict(),
                    "boundaries": [
                        "heartbeat observation time is runtime data, not deterministic provenance",
                        "TTL lease coordinator is controller-local, not distributed consensus",
                        "local content-addressed storage is not remote durability"
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
