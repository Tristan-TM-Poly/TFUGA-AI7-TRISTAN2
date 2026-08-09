from __future__ import annotations

import json
from pathlib import Path

from omega_game.engines.campaign import benchmark_campaign, merge_checkpoints, plan_campaign, run_campaign_slice
from omega_game.engines.evolution import seed_population
from omega_game.engines.game_spec import GameSpecCompiler
from omega_game.engines.simulation import ArenaConfig


def main() -> int:
    compiled = GameSpecCompiler().compile(
        Path(__file__).with_name("game_spec_fixed_layout.json").read_text(encoding="utf-8")
    )
    if not compiled.accepted or compiled.layout is None:
        raise SystemExit("fixed layout example did not compile")

    population = seed_population(4, seed=901)
    manifest = plan_campaign(
        population,
        layouts=(compiled.layout,),
        seeds=(1, 2),
        arena_template=ArenaConfig(max_steps=8),
        mirrored=True,
        shard_count=4,
    )

    # Backpressure + resume in small deterministic slices.
    checkpoint = None
    slices = []
    while checkpoint is None or len(checkpoint.completed) < manifest.job_count:
        checkpoint, report = run_campaign_slice(manifest, checkpoint=checkpoint, max_jobs=5)
        slices.append(report.to_dict())

    # Independent shard execution and deterministic merge.
    shard_checkpoints = []
    for shard in manifest.shards:
        piece, _ = run_campaign_slice(manifest, shard_ids=(shard.shard_id,))
        shard_checkpoints.append(piece)
    merged = merge_checkpoints(manifest, shard_checkpoints)
    if checkpoint.checkpoint_receipt != merged.checkpoint_receipt:
        raise SystemExit("sequential-resume and merged-shard receipts disagree")

    benchmark = benchmark_campaign(manifest, repetitions=2)
    print(
        json.dumps(
            {
                "plan_receipt": manifest.plan_receipt,
                "job_count": manifest.job_count,
                "shards": [shard.to_dict() for shard in manifest.shards],
                "slices": slices,
                "checkpoint_receipt": checkpoint.checkpoint_receipt,
                "merged_checkpoint_receipt": merged.checkpoint_receipt,
                "benchmark": benchmark.to_dict(),
                "boundary": "observed wall clock is empirical and excluded from deterministic receipts",
            },
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
