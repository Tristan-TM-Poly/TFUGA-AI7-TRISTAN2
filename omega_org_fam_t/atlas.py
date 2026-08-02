"""Streaming, sharded and reproducible atlas compiler."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .family_space import evidence_templates, iter_requested_cells
from .models import EvidenceTemplate, FamilyCell


@dataclass(frozen=True, slots=True)
class ShardRecord:
    path: str
    count: int
    sha256: str
    compressed_bytes: int


def _json_line(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_gzip_jsonl_shards(
    records: Iterable[dict[str, Any]],
    directory: Path,
    prefix: str,
    shard_size: int,
) -> tuple[int, list[ShardRecord]]:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob(f"{prefix}_*.jsonl.gz"):
        stale.unlink()
    total = 0
    shards: list[ShardRecord] = []
    handle: gzip.GzipFile | None = None
    path: Path | None = None
    count_in_shard = 0
    try:
        for record in records:
            if handle is None or count_in_shard >= shard_size:
                if handle is not None and path is not None:
                    handle.close()
                    shards.append(_shard_record(path, count_in_shard))
                path = directory / f"{prefix}_{len(shards):04d}.jsonl.gz"
                handle = gzip.GzipFile(filename=str(path), mode="wb", compresslevel=6, mtime=0)
                count_in_shard = 0
            handle.write(_json_line(record))
            count_in_shard += 1
            total += 1
    finally:
        if handle is not None and path is not None:
            handle.close()
            shards.append(_shard_record(path, count_in_shard))
    return total, shards


def _shard_record(path: Path, count: int) -> ShardRecord:
    payload = path.read_bytes()
    return ShardRecord(
        path=path.as_posix(),
        count=count,
        sha256=hashlib.sha256(payload).hexdigest(),
        compressed_bytes=len(payload),
    )


def iter_gzip_jsonl(paths: Iterable[Path]) -> Iterator[dict[str, Any]]:
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                yield json.loads(line)


def compile_atlas(
    output_dir: Path,
    *,
    family_records: int = 262_144,
    family_shard_size: int = 16_384,
    evidence_shard_size: int = 32_768,
) -> dict[str, Any]:
    if family_records < 0:
        raise ValueError("family_records must be non-negative")
    output_dir.mkdir(parents=True, exist_ok=True)
    family_dir = output_dir / "families"
    evidence_dir = output_dir / "evidence"

    family_count, family_shards = write_gzip_jsonl_shards(
        (cell.to_dict() for cell in iter_requested_cells(family_records)),
        family_dir,
        "family_cells",
        family_shard_size,
    )
    evidence_count, evidence_shards = write_gzip_jsonl_shards(
        (
            item.to_dict()
            for item in evidence_templates(iter_requested_cells(family_records))
        ),
        evidence_dir,
        "evidence_templates",
        evidence_shard_size,
    )
    manifest = {
        "version": "R0.1-massive",
        "family_records": family_count,
        "evidence_records": evidence_count,
        "total_objects": family_count + evidence_count,
        "family_shards": [{**asdict(s), "path": str(Path(s.path).relative_to(output_dir))} for s in family_shards],
        "evidence_shards": [{**asdict(s), "path": str(Path(s.path).relative_to(output_dir))} for s in evidence_shards],
        "generator": {
            "finite_experiment_parameter": family_records,
            "permanent_total_ceiling": None,
            "streaming": True,
            "compressed": True,
            "deterministic_gzip_mtime": 0,
        },
        "record_status": "machine_generated_family_space_candidates",
        "oak_boundary": (
            "The atlas enumerates candidate family-space cells and evidence templates. "
            "It does not certify molecular existence, stability, synthesis, identity, safety or utility."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def audit_atlas(output_dir: Path) -> dict[str, Any]:
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for section in ("family_shards", "evidence_shards"):
        for shard in manifest[section]:
            path = output_dir / Path(shard["path"])
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            results.append({
                "path": str(path),
                "exists": True,
                "sha256_matches": digest == shard["sha256"],
            })
    valid = all(item["sha256_matches"] for item in results)
    return {"valid": valid, "checked_shards": len(results), "results": results}
