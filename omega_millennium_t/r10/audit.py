from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from .compiler import MANIFEST_SCHEMA, _manifest
from .model import CellRecord, MerkleAccumulator, RuntimePolicy, stable_digest
from .store import AtlasStore


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _policy_from_checkpoint(checkpoint: Mapping[str, Any]) -> RuntimePolicy:
    value = checkpoint.get("policy", {})
    if not isinstance(value, Mapping):
        raise ValueError("checkpoint policy must be an object")
    return RuntimePolicy(
        batch_size=int(value["batch_size"]),
        shard_target_bytes=int(value["shard_target_bytes"]),
        max_disk_bytes=value.get("max_disk_bytes"),
        sqlite_busy_timeout_ms=int(value["sqlite_busy_timeout_ms"]),
    )


def _cell_from_row(row: sqlite3.Row) -> CellRecord:
    payload = json.loads(row["payload_json"])
    return CellRecord(
        cell_id=row["cell_id"],
        problem_id=row["problem_id"],
        target_id=row["target_id"],
        front=row["front"],
        method=row["method"],
        priority=int(row["priority"]),
        source_ref=row["source_ref"],
        payload=payload,
    )


def audit_streaming_atlas(output_dir: str | Path, *, chunk_size: int = 10_000) -> dict[str, Any]:
    output = Path(output_dir)
    errors: list[str] = []
    required = {"atlas.sqlite3", "manifest.json", "report.json"}
    present = {path.name for path in output.iterdir() if path.is_file()} if output.exists() else set()
    for name in sorted(required - present):
        errors.append(f"missing_file:{name}")
    if errors:
        return {
            "schema": "omega-problem-stream-audit/10",
            "valid": False,
            "errors": errors,
            "unlimited_capacity_claimed": False,
        }

    stored_manifest = _load_json(output / "manifest.json")
    stored_report = _load_json(output / "report.json")
    if stored_manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest_schema_mismatch")

    probe = sqlite3.connect(output / "atlas.sqlite3")
    probe.row_factory = sqlite3.Row
    checkpoint_row = probe.execute(
        "SELECT checkpoint_json, checkpoint_digest FROM checkpoints WHERE checkpoint_name='main'"
    ).fetchone()
    probe.close()
    if checkpoint_row is None:
        errors.append("checkpoint_missing")
        return {
            "schema": "omega-problem-stream-audit/10",
            "valid": False,
            "errors": errors,
            "unlimited_capacity_claimed": False,
        }
    checkpoint = json.loads(checkpoint_row["checkpoint_json"])
    if stable_digest(checkpoint) != checkpoint_row["checkpoint_digest"]:
        errors.append("checkpoint_digest_mismatch")

    policy = _policy_from_checkpoint(checkpoint)
    with AtlasStore(output / "atlas.sqlite3", policy) as store:
        replay_merkle = MerkleAccumulator()
        expected_sequence = 1
        replay_count = 0
        for chunk in store.iter_cells(chunk_size=chunk_size):
            for row in chunk:
                if int(row["sequence"]) != expected_sequence:
                    errors.append(f"cell_sequence_gap:{expected_sequence}->{row['sequence']}")
                    expected_sequence = int(row["sequence"])
                cell = _cell_from_row(row)
                if cell.digest != row["cell_digest"]:
                    errors.append(f"cell_digest_mismatch:{cell.cell_id}")
                replay_merkle.add_digest(cell.digest)
                replay_count += 1
                expected_sequence += 1

        checkpoint_merkle = MerkleAccumulator.from_dict(checkpoint["global_merkle"])
        if replay_merkle.leaf_count != checkpoint_merkle.leaf_count:
            errors.append("checkpoint_merkle_leaf_count_mismatch")
        if replay_merkle.root() != checkpoint_merkle.root():
            errors.append("checkpoint_merkle_root_mismatch")

        counts = store.counts()
        if replay_count != counts["cells"]:
            errors.append("cell_count_query_mismatch")
        if checkpoint.get("inserted_count") != counts["cells"]:
            errors.append("checkpoint_inserted_count_mismatch")
        if checkpoint.get("duplicate_count") != counts["duplicates"]:
            errors.append("checkpoint_duplicate_count_mismatch")
        if checkpoint.get("quarantine_count") != counts["quarantine"]:
            errors.append("checkpoint_quarantine_count_mismatch")

        for row in store.connection.execute("SELECT * FROM duplicates ORDER BY duplicate_id"):
            receipt = {
                "source_ordinal": int(row["source_ordinal"]),
                "cell_id": row["cell_id"],
                "existing_digest": row["existing_digest"],
                "incoming_digest": row["incoming_digest"],
                "exact_duplicate": bool(row["exact_duplicate"]),
            }
            if stable_digest(receipt) != row["receipt_digest"]:
                errors.append(f"duplicate_receipt_digest_mismatch:{row['duplicate_id']}")

        for row in store.connection.execute("SELECT * FROM quarantine ORDER BY quarantine_id"):
            receipt = {
                "source_ordinal": int(row["source_ordinal"]),
                "cell_id": row["cell_id"],
                "reason": row["reason"],
                "raw_digest": row["raw_digest"],
                "raw_excerpt": row["raw_excerpt"],
            }
            if stable_digest(receipt) != row["receipt_digest"]:
                errors.append(f"quarantine_receipt_digest_mismatch:{row['quarantine_id']}")

        for row in store.connection.execute("SELECT * FROM rollback_receipts ORDER BY rollback_id"):
            receipt = {
                "source_ordinal": int(row["source_ordinal"]),
                "reason": row["reason"],
                "checkpoint_digest": row["checkpoint_digest"],
            }
            if stable_digest(receipt) != row["receipt_digest"]:
                errors.append(f"rollback_receipt_digest_mismatch:{row['rollback_id']}")

        shard_rows = list(store.iter_shards())
        shard_cell_total = sum(int(row["row_count"]) for row in shard_rows)
        if checkpoint.get("complete") is True and shard_cell_total != replay_count:
            errors.append("shard_cell_total_mismatch")
        previous_last = 0
        for row in shard_rows:
            payload = {
                "shard_id": int(row["shard_id"]),
                "first_sequence": int(row["first_sequence"]),
                "last_sequence": int(row["last_sequence"]),
                "row_count": int(row["row_count"]),
                "byte_count": int(row["byte_count"]),
                "merkle_root": row["merkle_root"],
            }
            if stable_digest(payload) != row["shard_digest"]:
                errors.append(f"shard_digest_mismatch:{row['shard_id']}")
            if int(row["first_sequence"]) != previous_last + 1:
                errors.append(f"shard_sequence_gap:{row['shard_id']}")
            expected_rows = int(row["last_sequence"]) - int(row["first_sequence"]) + 1
            if expected_rows != int(row["row_count"]):
                errors.append(f"shard_row_count_mismatch:{row['shard_id']}")
            shard_merkle = MerkleAccumulator()
            cursor = store.connection.execute(
                "SELECT cell_digest FROM cells WHERE sequence BETWEEN ? AND ? ORDER BY sequence",
                (row["first_sequence"], row["last_sequence"]),
            )
            for cell_row in cursor:
                shard_merkle.add_digest(cell_row["cell_digest"])
            if shard_merkle.root() != row["merkle_root"]:
                errors.append(f"shard_merkle_mismatch:{row['shard_id']}")
            previous_last = int(row["last_sequence"])

        replay_manifest = _manifest(store, checkpoint)
        if replay_manifest != stored_manifest:
            errors.append("manifest_replay_mismatch")

    manifest_without_digest = {
        key: value for key, value in stored_manifest.items() if key != "manifest_digest"
    }
    if stable_digest(manifest_without_digest) != stored_manifest.get("manifest_digest"):
        errors.append("manifest_digest_invalid")
    report_without_digest = {
        key: value for key, value in stored_report.items() if key != "report_digest"
    }
    if stable_digest(report_without_digest) != stored_report.get("report_digest"):
        errors.append("report_digest_invalid")
    if stored_report.get("manifest_digest") != stored_manifest.get("manifest_digest"):
        errors.append("report_manifest_digest_mismatch")
    if stored_manifest.get("permanent_total_cell_cap") is not None:
        errors.append("permanent_total_cell_cap_present")
    if stored_manifest.get("unlimited_capacity_claimed") is not False:
        errors.append("unlimited_capacity_claim_detected")

    result = {
        "schema": "omega-problem-stream-audit/10",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "cell_count": stored_manifest.get("cell_count"),
        "shard_count": stored_manifest.get("shard_count"),
        "global_merkle_root": stored_manifest.get("global_merkle_root"),
        "complete": stored_manifest.get("complete"),
        "bounded_memory_proven": False,
        "unlimited_capacity_claimed": False,
        "permanent_total_cell_cap": None,
    }
    result["audit_digest"] = stable_digest(result)
    return result
