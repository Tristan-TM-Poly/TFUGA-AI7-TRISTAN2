from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .max_adapters import Adapter
from .max_models import digest_object


def shard_for_source(source_id: str, shard_count: int) -> int:
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    value = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:16], 16)
    return value % shard_count


def select_adapter_shard(
    adapters: Iterable[Adapter],
    *,
    shard_index: int,
    shard_count: int,
) -> tuple[Adapter, ...]:
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard_index must satisfy 0 <= shard_index < shard_count")
    return tuple(
        adapter
        for adapter in adapters
        if shard_for_source(adapter.source_id, shard_count) == shard_index
    )


def build_shard_matrix(shard_count: int) -> dict[str, object]:
    if shard_count < 1 or shard_count > 256:
        raise ValueError("shard_count must be between 1 and 256")
    return {
        "include": [
            {"shard_index": index, "shard_count": shard_count}
            for index in range(shard_count)
        ]
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _merkle_root(digests: Iterable[str]) -> str:
    layer = [bytes.fromhex(value) for value in sorted(digests)]
    if not layer:
        return hashlib.sha256(b"").hexdigest()
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[index] + layer[index + 1]).digest()
            for index in range(0, len(layer), 2)
        ]
    return layer[0].hex()


def aggregate_shards(
    input_root: str | Path,
    output_dir: str | Path,
    *,
    expected_shards: int | None = None,
) -> Path:
    source_root = Path(input_root)
    target_root = Path(output_dir)
    target_root.mkdir(parents=True, exist_ok=True)

    report_paths = sorted(source_root.rglob("campaign-report.json"))
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in report_paths]
    if not reports:
        raise ValueError("no shard campaign reports found")

    for report in reports:
        if (
            report.get("metadata_only") is not True
            or report.get("raw_bodies_persisted") is not False
            or report.get("full_text_collected") is not False
        ):
            raise ValueError("shard claim boundary violation")

    records_by_digest: dict[str, dict[str, object]] = {}
    receipts_by_digest: dict[str, dict[str, object]] = {}
    mminus_by_digest: dict[str, dict[str, object]] = {}
    shard_entries: list[dict[str, object]] = []

    for report_path, report in zip(report_paths, reports):
        shard_root = report_path.parent
        shard = report.get("shard") or {}
        shard_index = shard.get("index")
        shard_count = shard.get("count")
        shard_entries.append(
            {
                "shard_index": shard_index,
                "shard_count": shard_count,
                "report_sha256": report.get("report_sha256"),
                "record_count": report.get("record_count"),
                "request_count": report.get("request_count"),
                "mminus_count": report.get("mminus_count"),
                "relative_path": str(report_path.relative_to(source_root)),
            }
        )
        for row in _read_jsonl(shard_root / "records.jsonl"):
            digest = str(row.get("digest") or digest_object(row))
            records_by_digest[digest] = row
        for row in _read_jsonl(shard_root / "receipts.jsonl"):
            digest = str(row.get("digest") or digest_object(row))
            receipts_by_digest[digest] = row
        for row in _read_jsonl(shard_root / "mminus.jsonl"):
            digest = str(row.get("digest") or digest_object(row))
            mminus_by_digest[digest] = row

    records = sorted(
        records_by_digest.values(),
        key=lambda row: (
            str(row.get("source_id", "")),
            str(row.get("record_id", "")),
            str(row.get("digest", "")),
        ),
    )
    receipts = sorted(
        receipts_by_digest.values(),
        key=lambda row: (
            str(row.get("source_id", "")),
            str(row.get("request_id", "")),
            str(row.get("digest", "")),
        ),
    )
    mminus = sorted(
        mminus_by_digest.values(),
        key=lambda row: (
            str(row.get("source_id", "")),
            str(row.get("kind", "")),
            str(row.get("digest", "")),
        ),
    )

    _write_jsonl(target_root / "records.jsonl", records)
    _write_jsonl(target_root / "receipts.jsonl", receipts)
    _write_jsonl(target_root / "mminus.jsonl", mminus)

    discovered_indexes = sorted(
        {
            int(entry["shard_index"])
            for entry in shard_entries
            if entry.get("shard_index") is not None
        }
    )
    missing_shards: list[int] = []
    if expected_shards is not None:
        if expected_shards < 1:
            raise ValueError("expected_shards must be >= 1")
        missing_shards = sorted(set(range(expected_shards)) - set(discovered_indexes))

    source_counts = Counter(str(row.get("source_id", "")) for row in records)
    aggregate = {
        "schema": "omega-web-hg-r04-max-aggregate/1.0",
        "metadata_only": True,
        "raw_bodies_persisted": False,
        "full_text_collected": False,
        "permanent_total_cap": None,
        "expected_shards": expected_shards,
        "discovered_shards": discovered_indexes,
        "missing_shards": missing_shards,
        "complete": not missing_shards,
        "shard_reports": shard_entries,
        "record_count": len(records),
        "request_count": len(receipts),
        "mminus_count": len(mminus),
        "source_counts": dict(sorted(source_counts.items())),
        "record_merkle_root": _merkle_root(records_by_digest),
        "receipt_merkle_root": _merkle_root(receipts_by_digest),
        "mminus_merkle_root": _merkle_root(mminus_by_digest),
        "oak_boundaries": {
            "aggregate_is_complete_internet_absorption": False,
            "metadata_is_truth": False,
            "hash_is_semantic_validation": False,
            "missing_shards_are_silently_ignored": False,
        },
    }
    aggregate["report_sha256"] = digest_object(aggregate)
    (target_root / "aggregate-report.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target_root
