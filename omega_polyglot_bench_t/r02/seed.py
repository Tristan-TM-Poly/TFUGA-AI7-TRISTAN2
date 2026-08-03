"""Compact deterministic seed-atlas materializer (16,384 logical cells)."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


def materialize_seed_atlas(output_dir: Path, *, algorithms: int = 1024, shard_size: int = 4096) -> dict[str, object]:
    if algorithms < 1 or shard_size < 1:
        raise ValueError("algorithms and shard_size must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[list[int]] = []
    for algorithm_index in range(algorithms):
        for language_index in range(4):
            for strategy_index in range(4):
                parallelism_index = 4 if strategy_index == 3 else 0
                rows.append([len(rows), algorithm_index, language_index, strategy_index, 3, 0, parallelism_index, 0, 7, 0])
    shards: list[dict[str, object]] = []
    for number, offset in enumerate(range(0, len(rows), shard_size)):
        chunk = rows[offset:offset + shard_size]
        content = "\n".join(json.dumps(row, separators=(",", ":")) for row in chunk) + "\n"
        path = output_dir / f"research-cells-{number:04d}.jsonl"
        path.write_text(content, encoding="utf-8")
        shards.append({
            "path": path.name,
            "records": len(chunk),
            "sha256": sha256(content.encode()).hexdigest(),
            "first_seed_index": chunk[0][0],
            "last_seed_index": chunk[-1][0],
        })
    manifest: dict[str, object] = {
        "schema_version": "omega.polyglot-seed-atlas.v2",
        "encoding": "compact-json-array-v1",
        "columns": [
            "seed_index", "algorithm_index", "language_index", "strategy_index", "precision_index",
            "layout_index", "parallelism_index", "hardware_index", "objective_index", "gate_code",
        ],
        "records": len(rows),
        "algorithms": algorithms,
        "variants_per_algorithm_materialized": 16,
        "status": "LOGICAL_SEED_ONLY",
        "compiled_records": 0,
        "tested_records": 0,
        "benchmarked_records": 0,
        "scientific_validation_claimed": False,
        "universal_language_winner_claimed": False,
        "shards": shards,
    }
    (output_dir / "seed_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
