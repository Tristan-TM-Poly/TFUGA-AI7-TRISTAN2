from __future__ import annotations

import json
import tempfile
from pathlib import Path

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_runtime import (
    compare_process_execution,
    load_checkpoint,
    save_checkpoint,
)
from omega_game.engines.evolution import seed_population
from omega_game.engines.simulation import ArenaConfig


def main() -> int:
    manifest = plan_campaign(
        seed_population(4, seed=1001),
        seeds=(1, 2),
        arena_template=ArenaConfig(max_steps=8, resource_count=4),
        mirrored=True,
        shard_count=4,
    )

    checkpoint, first = run_campaign_slice(manifest, max_jobs=5)
    with tempfile.TemporaryDirectory(prefix="omega-game-r10-") as directory:
        path = Path(directory) / "checkpoint.json"
        save_receipt = save_checkpoint(path, checkpoint)
        restored, load_receipt = load_checkpoint(path, manifest)
        if restored.checkpoint_receipt != checkpoint.checkpoint_receipt:
            raise SystemExit("persisted checkpoint did not round-trip")
        restored, second = run_campaign_slice(manifest, checkpoint=restored, max_jobs=5)

    comparison = compare_process_execution(manifest, workers=2)
    print(
        json.dumps(
            {
                "plan_receipt": manifest.plan_receipt,
                "first_slice": first.to_dict(),
                "second_slice": second.to_dict(),
                "save_receipt": save_receipt.to_dict(),
                "load_receipt": load_receipt.to_dict(),
                "process_comparison": comparison.to_dict(),
                "boundaries": [
                    "lease ledger is controller-local, not distributed consensus",
                    "observed speedup is empirical and may be below 1",
                    "wall clock is excluded from deterministic provenance receipts"
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
