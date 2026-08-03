"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.10."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hardening import install_hardening

install_hardening()

from . import audit as _audit_module
from .compiler import _file_sha256, _run_campaign, materialize_synthetic_campaign
from .model import CELL_SCHEMA, RuntimePolicy, iter_jsonl, stable_digest
from .store import AtlasStore

_base_audit_streaming_atlas = _audit_module.audit_streaming_atlas


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


def audit_streaming_atlas(output_dir: str | Path, *, chunk_size: int = 10_000) -> dict[str, Any]:
    output = Path(output_dir)
    result = _base_audit_streaming_atlas(output, chunk_size=chunk_size)
    errors = list(result.get("errors", []))
    manifest_path = output / "manifest.json"
    report_path = output / "report.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = (
            json.loads(report_path.read_text(encoding="utf-8"))
            if report_path.exists()
            else {}
        )
        compatibility = manifest.get("source_compatibility")
        if manifest.get("source_kind") == "r03_max" and compatibility is None:
            errors.append("r03_compatibility_receipt_required")
        if compatibility is not None:
            receipt_path = output / "r03_compatibility.json"
            if not receipt_path.exists():
                errors.append("r03_compatibility_file_missing")
            else:
                stored = json.loads(receipt_path.read_text(encoding="utf-8"))
                if stored != compatibility:
                    errors.append("r03_compatibility_manifest_mismatch")
                digest_view = {
                    key: value for key, value in stored.items() if key != "receipt_digest"
                }
                if stable_digest(digest_view) != stored.get("receipt_digest"):
                    errors.append("r03_compatibility_receipt_digest_invalid")
                if stored.get("valid") is not True:
                    errors.append("r03_compatibility_receipt_not_valid")
                if stored.get("finite_fixture_is_not_unlimited_capacity_proof") is not True:
                    errors.append("r03_finite_fixture_disclaimer_missing")
                expected_report_fields = {
                    "r03_compatibility_receipt_digest": stored.get("receipt_digest"),
                    "r03_manifest_digest_reproduced": stored.get("r03_manifest_digest"),
                    "r03_report_digest_reproduced": stored.get("r03_report_digest"),
                }
                for key, expected in expected_report_fields.items():
                    if report.get(key) != expected:
                        errors.append(f"r03_report_binding_mismatch:{key}")
                if manifest.get("source_digest") != stored.get("r03_manifest_digest"):
                    errors.append("r03_source_digest_binding_mismatch")
    result["errors"] = sorted(set(errors))
    result["valid"] = not result["errors"]
    result.pop("audit_digest", None)
    result["audit_digest"] = stable_digest(result)
    return result


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
