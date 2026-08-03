from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .model import (
    CELL_SCHEMA,
    REPORT_SCHEMA,
    CellRecord,
    MerkleAccumulator,
    RuntimePolicy,
    canonical_json,
    iter_jsonl,
    stable_digest,
    write_json,
)
from .store import AtlasStore

CHECKPOINT_SCHEMA = "omega-problem-stream-checkpoint/10"
MANIFEST_SCHEMA = "omega-problem-stream-manifest/10"


def _file_sha256(path: Path, chunk_bytes: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _initial_state(source_kind: str, source_digest: str, policy: RuntimePolicy) -> dict[str, Any]:
    return {
        "schema": CHECKPOINT_SCHEMA,
        "source_kind": source_kind,
        "source_digest": source_digest,
        "next_source_ordinal": 1,
        "next_sequence": 1,
        "input_rows_seen": 0,
        "inserted_count": 0,
        "duplicate_count": 0,
        "quarantine_count": 0,
        "complete": False,
        "global_merkle": MerkleAccumulator().to_dict(),
        "shard_state": {
            "shard_id": 1,
            "first_sequence": None,
            "last_sequence": None,
            "row_count": 0,
            "byte_count": 0,
            "merkle": MerkleAccumulator().to_dict(),
        },
        "policy": policy.to_dict(),
    }


def _restore_or_initialize(
    store: AtlasStore,
    source_kind: str,
    source_digest: str,
    policy: RuntimePolicy,
    resume: bool,
) -> dict[str, Any]:
    checkpoint = store.load_checkpoint()
    if checkpoint is None:
        if resume:
            raise ValueError("resume_requested_without_checkpoint")
        state = _initial_state(source_kind, source_digest, policy)
        with store.transaction():
            store.save_checkpoint(state)
        return state
    if not resume:
        raise ValueError("existing_checkpoint_requires_resume_or_clean_output")
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("checkpoint_schema_mismatch")
    if checkpoint.get("source_kind") != source_kind:
        raise ValueError("checkpoint_source_kind_mismatch")
    if checkpoint.get("source_digest") != source_digest:
        raise ValueError("checkpoint_source_digest_mismatch")
    if checkpoint.get("policy") != policy.to_dict():
        raise ValueError("checkpoint_policy_mismatch")
    return checkpoint


def _finalize_current_shard(store: AtlasStore, state: dict[str, Any]) -> None:
    shard_state = state["shard_state"]
    if shard_state["row_count"] == 0:
        return
    merkle = MerkleAccumulator.from_dict(shard_state["merkle"])
    store.add_shard(
        {
            "shard_id": shard_state["shard_id"],
            "first_sequence": shard_state["first_sequence"],
            "last_sequence": shard_state["last_sequence"],
            "row_count": shard_state["row_count"],
            "byte_count": shard_state["byte_count"],
            "merkle_root": merkle.root(),
        }
    )
    state["shard_state"] = {
        "shard_id": shard_state["shard_id"] + 1,
        "first_sequence": None,
        "last_sequence": None,
        "row_count": 0,
        "byte_count": 0,
        "merkle": MerkleAccumulator().to_dict(),
    }


def _add_inserted_to_state(
    store: AtlasStore,
    state: dict[str, Any],
    cell: CellRecord,
    serialized_bytes: int,
    policy: RuntimePolicy,
) -> None:
    shard_state = state["shard_state"]
    if (
        shard_state["row_count"] > 0
        and shard_state["byte_count"] + serialized_bytes > policy.shard_target_bytes
    ):
        _finalize_current_shard(store, state)
        shard_state = state["shard_state"]

    sequence = state["next_sequence"]
    shard_merkle = MerkleAccumulator.from_dict(shard_state["merkle"])
    shard_merkle.add_digest(cell.digest)
    global_merkle = MerkleAccumulator.from_dict(state["global_merkle"])
    global_merkle.add_digest(cell.digest)

    if shard_state["first_sequence"] is None:
        shard_state["first_sequence"] = sequence
    shard_state["last_sequence"] = sequence
    shard_state["row_count"] += 1
    shard_state["byte_count"] += serialized_bytes
    shard_state["merkle"] = shard_merkle.to_dict()
    state["global_merkle"] = global_merkle.to_dict()
    state["next_sequence"] += 1
    state["inserted_count"] += 1


def _process_batch(
    store: AtlasStore,
    state: dict[str, Any],
    batch: list[tuple[int, Mapping[str, Any], str]],
    policy: RuntimePolicy,
) -> None:
    before = copy.deepcopy(state)
    try:
        with store.transaction():
            for source_ordinal, raw_row, raw_text in batch:
                state["input_rows_seen"] += 1
                state["next_source_ordinal"] = source_ordinal + 1
                try:
                    cell = CellRecord.from_dict(raw_row)
                except Exception as exc:
                    store.quarantine(
                        source_ordinal,
                        f"invalid_cell:{type(exc).__name__}:{exc}",
                        raw_text,
                        cell_id=str(raw_row.get("cell_id", "")).strip() or None,
                    )
                    state["quarantine_count"] += 1
                    continue

                sequence = state["next_sequence"]
                outcome = store.insert_cell(sequence, source_ordinal, cell)
                if outcome == "inserted":
                    _add_inserted_to_state(
                        store,
                        state,
                        cell,
                        len(canonical_json(cell.to_dict()).encode("utf-8")) + 1,
                        policy,
                    )
                elif outcome == "duplicate":
                    state["duplicate_count"] += 1
                else:
                    state["duplicate_count"] += 1
                    state["quarantine_count"] += 1
                store.enforce_disk_budget()
            store.save_checkpoint(state)
    except Exception:
        state.clear()
        state.update(before)
        raise


def _iter_synthetic(
    cell_count: int,
    *,
    start_ordinal: int,
    problem_count: int,
    target_count: int,
    fronts: tuple[str, ...],
    methods: tuple[str, ...],
) -> Iterator[tuple[int, Mapping[str, Any], str]]:
    for ordinal in range(start_ordinal, cell_count + 1):
        index = ordinal - 1
        problem_index = index % problem_count
        target_index = (index // problem_count) % target_count
        front = fronts[(index // (problem_count * target_count)) % len(fronts)]
        method = methods[(index // max(1, len(fronts))) % len(methods)]
        priority = int(hashlib.sha256(f"priority:{index}".encode()).hexdigest()[:8], 16) % 10_000
        row = {
            "schema": CELL_SCHEMA,
            "cell_id": f"synthetic::cell::{index:016d}",
            "problem_id": f"synthetic::problem::{problem_index:06d}",
            "target_id": f"synthetic::target::{target_index:06d}",
            "front": front,
            "method": method,
            "priority": priority,
            "source_ref": f"synthetic://campaign/{index}",
            "payload": {
                "logical_index": index,
                "problem_index": problem_index,
                "target_index": target_index,
                "synthetic": True,
            },
        }
        raw = canonical_json(row) + "\n"
        yield ordinal, row, raw


def _take_batches(
    rows: Iterable[tuple[int, Mapping[str, Any], str]],
    *,
    batch_size: int,
    max_items: int | None,
) -> Iterator[list[tuple[int, Mapping[str, Any], str]]]:
    batch: list[tuple[int, Mapping[str, Any], str]] = []
    emitted = 0
    for row in rows:
        if max_items is not None and emitted >= max_items:
            break
        batch.append(row)
        emitted += 1
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _manifest(store: AtlasStore, state: Mapping[str, Any]) -> dict[str, Any]:
    counts = store.counts()
    global_merkle = MerkleAccumulator.from_dict(state["global_merkle"])
    shards = [
        {
            "shard_id": int(row["shard_id"]),
            "first_sequence": int(row["first_sequence"]),
            "last_sequence": int(row["last_sequence"]),
            "row_count": int(row["row_count"]),
            "byte_count": int(row["byte_count"]),
            "merkle_root": row["merkle_root"],
            "shard_digest": row["shard_digest"],
        }
        for row in store.iter_shards()
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "source_kind": state["source_kind"],
        "source_digest": state["source_digest"],
        "complete": state["complete"],
        "input_rows_seen": state["input_rows_seen"],
        "inserted_count": state["inserted_count"],
        "duplicate_count": state["duplicate_count"],
        "quarantine_count": state["quarantine_count"],
        "cell_count": counts["cells"],
        "duplicate_ledger_count": counts["duplicates"],
        "quarantine_ledger_count": counts["quarantine"],
        "rollback_receipt_count": counts["rollback_receipts"],
        "shard_count": counts["shards"],
        "global_merkle_root": global_merkle.root(),
        "global_merkle_leaf_count": global_merkle.leaf_count,
        "shards": shards,
        "policy": state["policy"],
        "permanent_total_cell_cap": None,
        "unlimited_capacity_claimed": False,
    }
    manifest["manifest_digest"] = stable_digest(manifest)
    return manifest


def _write_outputs(output: Path, report: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    write_json(output / "manifest.json", manifest)
    write_json(output / "report.json", report)


def _run_campaign(
    *,
    output_dir: str | Path,
    source_kind: str,
    source_digest: str,
    rows: Iterable[tuple[int, Mapping[str, Any], str]],
    policy: RuntimePolicy,
    resume: bool,
    max_items: int | None,
    expected_total_rows: int | None,
    clean: bool,
) -> dict[str, Any]:
    output = Path(output_dir)
    if output.exists() and clean and not resume:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    db_path = output / "atlas.sqlite3"

    with AtlasStore(db_path, policy) as store:
        state = _restore_or_initialize(store, source_kind, source_digest, policy, resume)
        if state.get("complete") is True:
            manifest = _manifest(store, state)
            report = {
                "schema": REPORT_SCHEMA,
                "status": "already_complete",
                "complete": True,
                "manifest_digest": manifest["manifest_digest"],
                "cell_count": manifest["cell_count"],
                "peak_memory_independent_of_total_claimed": False,
                "unlimited_capacity_claimed": False,
                "permanent_total_cell_cap": None,
            }
            report["report_digest"] = stable_digest(report)
            _write_outputs(output, report, manifest)
            return report

        failure: str | None = None
        rollback_digest: str | None = None
        try:
            for batch in _take_batches(rows, batch_size=policy.batch_size, max_items=max_items):
                _process_batch(store, state, batch, policy)
        except Exception as exc:
            failure = f"{type(exc).__name__}:{exc}"
            checkpoint = store.load_checkpoint()
            rollback_digest = store.record_rollback(
                state.get("next_source_ordinal", 1),
                failure,
                stable_digest(checkpoint) if checkpoint is not None else None,
            )

        if failure is None:
            reached_end = expected_total_rows is not None and state["next_source_ordinal"] > expected_total_rows
            if reached_end:
                with store.transaction():
                    _finalize_current_shard(store, state)
                    state["complete"] = True
                    store.save_checkpoint(state)

        manifest = _manifest(store, state)
        report = {
            "schema": REPORT_SCHEMA,
            "status": "failed" if failure else ("complete" if state["complete"] else "checkpointed"),
            "complete": state["complete"],
            "failure": failure,
            "rollback_receipt_digest": rollback_digest,
            "manifest_digest": manifest["manifest_digest"],
            "cell_count": manifest["cell_count"],
            "input_rows_seen": manifest["input_rows_seen"],
            "duplicate_count": manifest["duplicate_count"],
            "quarantine_count": manifest["quarantine_count"],
            "shard_count": manifest["shard_count"],
            "database_bytes": store.database_bytes(),
            "batch_size": policy.batch_size,
            "peak_memory_independent_of_total_claimed": False,
            "unlimited_capacity_claimed": False,
            "permanent_total_cell_cap": None,
        }
        report["report_digest"] = stable_digest(report)
        _write_outputs(output, report, manifest)
        return report


def ingest_jsonl(
    input_jsonl: str | Path,
    output_dir: str | Path,
    *,
    policy: RuntimePolicy | None = None,
    resume: bool = False,
    max_items: int | None = None,
    clean: bool = True,
) -> dict[str, Any]:
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
    total_rows = sum(1 for _ in source.open("r", encoding="utf-8"))
    return _run_campaign(
        output_dir=output,
        source_kind="jsonl",
        source_digest=source_digest,
        rows=rows,
        policy=runtime,
        resume=resume,
        max_items=max_items,
        expected_total_rows=total_rows,
        clean=clean,
    )


def materialize_synthetic_campaign(
    output_dir: str | Path,
    *,
    cell_count: int,
    problem_count: int = 72,
    target_count: int = 16,
    fronts: tuple[str, ...] = ("analysis", "algebra", "geometry", "computation"),
    methods: tuple[str, ...] = ("exact", "interval", "sat", "formal"),
    policy: RuntimePolicy | None = None,
    resume: bool = False,
    max_items: int | None = None,
    clean: bool = True,
) -> dict[str, Any]:
    if cell_count < 0:
        raise ValueError("cell_count must be non-negative")
    if problem_count < 1 or target_count < 1 or not fronts or not methods:
        raise ValueError("synthetic dimensions must be non-empty and positive")
    runtime = policy or RuntimePolicy()
    descriptor = {
        "cell_count": cell_count,
        "problem_count": problem_count,
        "target_count": target_count,
        "fronts": list(fronts),
        "methods": list(methods),
    }
    source_digest = stable_digest(descriptor)
    start = 1
    output = Path(output_dir)
    if resume and (output / "atlas.sqlite3").exists():
        with AtlasStore(output / "atlas.sqlite3", runtime) as store:
            checkpoint = store.load_checkpoint()
            if checkpoint is not None:
                start = int(checkpoint["next_source_ordinal"])
    rows = _iter_synthetic(
        cell_count,
        start_ordinal=start,
        problem_count=problem_count,
        target_count=target_count,
        fronts=fronts,
        methods=methods,
    )
    return _run_campaign(
        output_dir=output,
        source_kind="synthetic",
        source_digest=source_digest,
        rows=rows,
        policy=runtime,
        resume=resume,
        max_items=max_items,
        expected_total_rows=cell_count,
        clean=clean,
    )
