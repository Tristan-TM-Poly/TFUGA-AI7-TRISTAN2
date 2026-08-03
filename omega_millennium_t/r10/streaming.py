"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.10."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_streaming_atlas
from .compiler import (
    _file_sha256,
    _run_campaign,
    ingest_jsonl as _base_ingest_jsonl,
    materialize_synthetic_campaign,
)
from .model import CELL_SCHEMA, RuntimePolicy, iter_jsonl, stable_digest
from .store import AtlasStore


def _last_nonempty_line(path: Path) -> int:
    last = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                last = line_number
    return last


def ingest_jsonl(
    input_jsonl: str | Path,
    output_dir: str | Path,
    *,
    policy: RuntimePolicy | None = None,
    resume: bool = False,
    max_items: int | None = None,
    clean: bool = True,
) -> dict[str, Any]:
    """Ingest JSONL while treating blank lines as non-records for completion."""
    source = Path(input_jsonl)
    runtime = policy or RuntimePolicy()
    source_digest = _file_sha256(source)
    start = 1
    output = Path(output_dir)
    if resume and (output / "atlas.sqlite3").exists():
        with AtlasStore(output / "atlas.sqlite3", runtime) as store:
            checkpoint = store.load_checkpoint()
            if checkpoint is not None:
                start = int(checkpoint["next_source_ordinal"])
    rows = iter_jsonl(source, start_line=start)
    return _run_campaign(
        output_dir=output,
        source_kind="jsonl",
        source_digest=source_digest,
        rows=rows,
        policy=runtime,
        resume=resume,
        max_items=max_items,
        expected_total_rows=_last_nonempty_line(source),
        clean=clean,
    )


def query_portfolio(
    output_dir: str | Path,
    *,
    limit: int = 24,
    max_per_front: int = 2,
    min_priority: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    db_path = output / "atlas.sqlite3"
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    import sqlite3

    probe = sqlite3.connect(db_path)
    probe.row_factory = sqlite3.Row
    row = probe.execute(
        "SELECT checkpoint_json FROM checkpoints WHERE checkpoint_name='main'"
    ).fetchone()
    probe.close()
    if row is None:
        raise ValueError("checkpoint_missing")
    checkpoint = json.loads(row["checkpoint_json"])
    policy_data = checkpoint["policy"]
    policy = RuntimePolicy(
        batch_size=int(policy_data["batch_size"]),
        shard_target_bytes=int(policy_data["shard_target_bytes"]),
        max_disk_bytes=policy_data.get("max_disk_bytes"),
        sqlite_busy_timeout_ms=int(policy_data["sqlite_busy_timeout_ms"]),
    )
    with AtlasStore(db_path, policy) as store:
        rows = store.query_portfolio(
            limit=limit,
            max_per_front=max_per_front,
            min_priority=min_priority,
        )
        total_cells = store.counts()["cells"]
    result = {
        "schema": "omega-problem-stream-portfolio/10",
        "limit": limit,
        "max_per_front": max_per_front,
        "min_priority": min_priority,
        "selected_count": len(rows),
        "total_cell_count": total_cells,
        "rows": rows,
        "full_atlas_loaded": False,
        "query_engine": "sqlite_window_function",
        "permanent_total_cell_cap": None,
        "unlimited_capacity_claimed": False,
    }
    result["query_digest"] = stable_digest(result)
    return result


__all__ = [
    "CELL_SCHEMA",
    "audit_streaming_atlas",
    "ingest_jsonl",
    "materialize_synthetic_campaign",
    "query_portfolio",
]
