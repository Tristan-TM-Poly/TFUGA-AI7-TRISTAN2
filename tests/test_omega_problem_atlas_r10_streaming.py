from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from omega_millennium_t.r10 import (
    audit_streaming_atlas,
    ingest_jsonl,
    materialize_synthetic_campaign,
    query_portfolio,
)
from omega_millennium_t.r10.model import CELL_SCHEMA, RuntimePolicy


def _policy(*, batch_size: int = 257, shard_bytes: int = 32_768, max_disk: int | None = None) -> RuntimePolicy:
    return RuntimePolicy(
        batch_size=batch_size,
        shard_target_bytes=shard_bytes,
        max_disk_bytes=max_disk,
    )


def _manifest(output: Path) -> dict:
    return json.loads((output / "manifest.json").read_text(encoding="utf-8"))


def _cell(index: int, **overrides) -> dict:
    row = {
        "schema": CELL_SCHEMA,
        "cell_id": f"cell::{index:06d}",
        "problem_id": f"problem::{index % 5}",
        "target_id": f"target::{index % 3}",
        "front": ("analysis", "algebra", "geometry")[index % 3],
        "method": ("exact", "interval")[index % 2],
        "priority": 1000 - index,
        "source_ref": f"fixture://cell/{index}",
        "payload": {"index": index},
    }
    row.update(overrides)
    return row


def _write_jsonl(path: Path, rows: list[dict | str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row)
                if not row.endswith("\n"):
                    handle.write("\n")
            else:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


def test_synthetic_campaign_is_deterministic(tmp_path: Path) -> None:
    policy = _policy()
    output_a = tmp_path / "a"
    output_b = tmp_path / "b"
    report_a = materialize_synthetic_campaign(output_a, cell_count=10_000, policy=policy)
    report_b = materialize_synthetic_campaign(output_b, cell_count=10_000, policy=policy)
    assert report_a["complete"] is True
    assert report_b["complete"] is True
    assert _manifest(output_a) == _manifest(output_b)
    assert audit_streaming_atlas(output_a)["valid"] is True
    assert audit_streaming_atlas(output_b)["valid"] is True


def test_interruption_and_resume_match_uninterrupted_manifest(tmp_path: Path) -> None:
    policy = _policy(batch_size=211, shard_bytes=24_000)
    uninterrupted = tmp_path / "full"
    resumed = tmp_path / "resumed"
    materialize_synthetic_campaign(uninterrupted, cell_count=7_500, policy=policy)
    first = materialize_synthetic_campaign(
        resumed,
        cell_count=7_500,
        policy=policy,
        max_items=1_337,
    )
    assert first["status"] == "checkpointed"
    assert first["complete"] is False
    second = materialize_synthetic_campaign(
        resumed,
        cell_count=7_500,
        policy=policy,
        resume=True,
        clean=False,
    )
    assert second["complete"] is True
    assert _manifest(resumed) == _manifest(uninterrupted)
    assert audit_streaming_atlas(resumed)["valid"] is True


def test_jsonl_blank_lines_do_not_prevent_completion(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    _write_jsonl(source, [_cell(0), "", "   ", _cell(1), "", _cell(2)])
    output = tmp_path / "out"
    report = ingest_jsonl(source, output, policy=_policy(batch_size=2))
    assert report["complete"] is True
    assert report["cell_count"] == 3
    assert audit_streaming_atlas(output)["valid"] is True


def test_exact_duplicate_enters_duplicate_ledger(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    first = _cell(0)
    _write_jsonl(source, [first, first, _cell(1)])
    output = tmp_path / "out"
    report = ingest_jsonl(source, output, policy=_policy(batch_size=2))
    assert report["cell_count"] == 2
    assert report["duplicate_count"] == 1
    manifest = _manifest(output)
    assert manifest["duplicate_ledger_count"] == 1
    assert manifest["quarantine_ledger_count"] == 0


def test_duplicate_id_digest_conflict_is_quarantined(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    first = _cell(0)
    conflict = _cell(0, priority=9999)
    _write_jsonl(source, [first, conflict])
    output = tmp_path / "out"
    report = ingest_jsonl(source, output, policy=_policy())
    assert report["cell_count"] == 1
    assert report["duplicate_count"] == 1
    assert report["quarantine_count"] == 1
    assert audit_streaming_atlas(output)["valid"] is True


def test_invalid_cell_is_quarantined_and_stream_continues(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    invalid = _cell(1)
    invalid["priority"] = "high"
    _write_jsonl(source, [_cell(0), invalid, _cell(2)])
    output = tmp_path / "out"
    report = ingest_jsonl(source, output, policy=_policy(batch_size=3))
    assert report["complete"] is True
    assert report["cell_count"] == 2
    assert report["quarantine_count"] == 1


def test_malformed_json_produces_rollback_receipt(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    _write_jsonl(source, [_cell(0), _cell(1), _cell(2), "{malformed"])
    output = tmp_path / "out"
    report = ingest_jsonl(source, output, policy=_policy(batch_size=2))
    assert report["status"] == "failed"
    assert report["rollback_receipt_digest"] is not None
    assert report["cell_count"] == 2
    manifest = _manifest(output)
    assert manifest["rollback_receipt_count"] == 1
    assert audit_streaming_atlas(output)["valid"] is True


def test_disk_budget_failure_rolls_back_batch(tmp_path: Path) -> None:
    output = tmp_path / "out"
    report = materialize_synthetic_campaign(
        output,
        cell_count=100,
        policy=_policy(batch_size=25, max_disk=1),
    )
    assert report["status"] == "failed"
    assert report["cell_count"] == 0
    assert report["rollback_receipt_digest"] is not None
    assert _manifest(output)["rollback_receipt_count"] == 1


def test_portfolio_query_is_bounded_and_diversified(tmp_path: Path) -> None:
    output = tmp_path / "out"
    materialize_synthetic_campaign(output, cell_count=5_000, policy=_policy())
    result = query_portfolio(output, limit=12, max_per_front=2, min_priority=100)
    assert result["selected_count"] <= 8
    assert result["full_atlas_loaded"] is False
    assert result["total_cell_count"] == 5_000
    counts: dict[str, int] = {}
    for row in result["rows"]:
        counts[row["front"]] = counts.get(row["front"], 0) + 1
    assert max(counts.values()) <= 2


def test_audit_detects_cell_digest_tampering(tmp_path: Path) -> None:
    output = tmp_path / "out"
    materialize_synthetic_campaign(output, cell_count=1_000, policy=_policy())
    connection = sqlite3.connect(output / "atlas.sqlite3")
    connection.execute("UPDATE cells SET cell_digest=? WHERE sequence=1", ("0" * 64,))
    connection.commit()
    connection.close()
    audit = audit_streaming_atlas(output)
    assert audit["valid"] is False
    assert any(item.startswith("cell_digest_mismatch:") for item in audit["errors"])


def test_resume_rejects_policy_change(tmp_path: Path) -> None:
    output = tmp_path / "out"
    materialize_synthetic_campaign(
        output,
        cell_count=1_000,
        policy=_policy(batch_size=100),
        max_items=100,
    )
    with pytest.raises(ValueError, match="checkpoint_policy_mismatch"):
        materialize_synthetic_campaign(
            output,
            cell_count=1_000,
            policy=_policy(batch_size=101),
            resume=True,
            clean=False,
        )


def test_resume_rejects_modified_jsonl_source(tmp_path: Path) -> None:
    source = tmp_path / "cells.jsonl"
    _write_jsonl(source, [_cell(index) for index in range(20)])
    output = tmp_path / "out"
    ingest_jsonl(source, output, policy=_policy(batch_size=5), max_items=5)
    with source.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_cell(21)) + "\n")
    with pytest.raises(ValueError, match="checkpoint_source_digest_mismatch"):
        ingest_jsonl(source, output, policy=_policy(batch_size=5), resume=True, clean=False)


def test_million_cell_campaign_can_checkpoint_without_materializing_all(tmp_path: Path) -> None:
    output = tmp_path / "million-logical"
    report = materialize_synthetic_campaign(
        output,
        cell_count=1_000_000,
        policy=_policy(batch_size=100),
        max_items=500,
    )
    assert report["status"] == "checkpointed"
    assert report["cell_count"] == 500
    manifest = _manifest(output)
    assert manifest["permanent_total_cell_cap"] is None
    assert manifest["unlimited_capacity_claimed"] is False
    connection = sqlite3.connect(output / "atlas.sqlite3")
    checkpoint = json.loads(
        connection.execute(
            "SELECT checkpoint_json FROM checkpoints WHERE checkpoint_name='main'"
        ).fetchone()[0]
    )
    connection.close()
    assert checkpoint["source_kind"] == "synthetic"
    assert checkpoint["next_source_ordinal"] == 501


def test_no_permanent_total_cap_is_encoded(tmp_path: Path) -> None:
    output = tmp_path / "out"
    materialize_synthetic_campaign(output, cell_count=100, policy=_policy())
    manifest = _manifest(output)
    assert manifest["policy"]["permanent_total_cell_cap"] is None
    assert manifest["permanent_total_cell_cap"] is None
