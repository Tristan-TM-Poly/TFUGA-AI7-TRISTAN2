"""Sharded, atomic local storage for finite Ω-VLA campaigns."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ShardReceipt:
    path: str
    records: int
    bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StoreManifest:
    format: str
    records: int
    shards: tuple[ShardReceipt, ...]
    aggregate_sha256: str
    checkpoint_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "records": self.records,
            "shards": [shard.to_dict() for shard in self.shards],
            "aggregate_sha256": self.aggregate_sha256,
            "checkpoint_path": self.checkpoint_path,
        }


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


class ShardedJSONLStore:
    """Write bounded JSONL shards and deterministic manifests."""

    def __init__(
        self,
        root: str | Path,
        *,
        records_per_shard: int = 1024,
        prefix: str = "cells",
    ) -> None:
        if records_per_shard <= 0:
            raise ValueError("records_per_shard must be positive")
        self.root = Path(root)
        self.records_per_shard = int(records_per_shard)
        self.prefix = prefix
        self.shard_dir = self.root / "shards"
        self.checkpoint_path = self.root / "checkpoint.json"
        self.manifest_path = self.root / "manifest.json"

    def write(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        checkpoint: Mapping[str, Any],
    ) -> StoreManifest:
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        receipts: list[ShardReceipt] = []
        batch: list[Mapping[str, Any]] = []
        total = 0
        shard_index = 0

        def flush() -> None:
            nonlocal batch, shard_index, total
            if not batch:
                return
            lines = [
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for record in batch
            ]
            content = "\n".join(lines) + "\n"
            path = self.shard_dir / f"{self.prefix}-{shard_index:06d}.jsonl"
            atomic_write_text(path, content)
            encoded = content.encode("utf-8")
            receipts.append(
                ShardReceipt(
                    path=str(path.relative_to(self.root)),
                    records=len(batch),
                    bytes=len(encoded),
                    sha256=sha256(encoded).hexdigest(),
                )
            )
            total += len(batch)
            shard_index += 1
            batch = []

        for record in records:
            batch.append(record)
            if len(batch) >= self.records_per_shard:
                flush()
        flush()

        aggregate = sha256(
            "".join(receipt.sha256 for receipt in receipts).encode("ascii")
        ).hexdigest()
        atomic_write_json(self.checkpoint_path, checkpoint)
        manifest = StoreManifest(
            format="jsonl-sharded-v1",
            records=total,
            shards=tuple(receipts),
            aggregate_sha256=aggregate,
            checkpoint_path=str(self.checkpoint_path.relative_to(self.root)),
        )
        atomic_write_json(self.manifest_path, manifest.to_dict())
        return manifest

    def read_manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def read_checkpoint(self) -> dict[str, Any]:
        return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
