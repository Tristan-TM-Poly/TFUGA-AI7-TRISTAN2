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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ShardReceipt":
        return cls(
            path=str(payload["path"]),
            records=int(payload["records"]),
            bytes=int(payload["bytes"]),
            sha256=str(payload["sha256"]),
        )


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


class StreamingShardedJSONLWriter:
    """Incrementally write shards with replayable state.

    Checkpoints flush the current buffer first, so a checkpoint never points
    beyond durable shard content. Resume verifies recorded shard hashes before
    accepting new records.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        records_per_shard: int = 1024,
        prefix: str = "cells",
        resume: bool = False,
        reset: bool = False,
    ) -> None:
        if records_per_shard <= 0:
            raise ValueError("records_per_shard must be positive")
        if resume and reset:
            raise ValueError("resume and reset are mutually exclusive")
        self.root = Path(root)
        self.records_per_shard = int(records_per_shard)
        self.prefix = prefix
        self.shard_dir = self.root / "shards"
        self.checkpoint_path = self.root / "checkpoint.json"
        self.manifest_path = self.root / "manifest.json"
        self.state_path = self.root / "writer-state.json"
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: list[Mapping[str, Any]] = []
        self._receipts: list[ShardReceipt] = []
        self._total = 0
        self._next_shard_index = 0

        if reset:
            self._reset_files()
        elif resume:
            self._load_state()
        elif any(self.shard_dir.glob(f"{self.prefix}-*.jsonl")):
            raise FileExistsError(
                "existing shards found; select resume=True or reset=True"
            )

    @property
    def records(self) -> int:
        return self._total + len(self._buffer)

    @property
    def durable_records(self) -> int:
        return self._total

    def add(self, record: Mapping[str, Any]) -> None:
        self._buffer.append(record)
        if len(self._buffer) >= self.records_per_shard:
            self.flush()

    def extend(self, records: Iterable[Mapping[str, Any]]) -> None:
        for record in records:
            self.add(record)

    def flush(self) -> ShardReceipt | None:
        if not self._buffer:
            return None
        lines = [
            json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            for record in self._buffer
        ]
        content = "\n".join(lines) + "\n"
        path = self.shard_dir / f"{self.prefix}-{self._next_shard_index:06d}.jsonl"
        atomic_write_text(path, content)
        encoded = content.encode("utf-8")
        receipt = ShardReceipt(
            path=str(path.relative_to(self.root)),
            records=len(self._buffer),
            bytes=len(encoded),
            sha256=sha256(encoded).hexdigest(),
        )
        self._receipts.append(receipt)
        self._total += len(self._buffer)
        self._next_shard_index += 1
        self._buffer = []
        self._write_state()
        return receipt

    def checkpoint(self, payload: Mapping[str, Any]) -> None:
        self.flush()
        enriched = dict(payload)
        enriched["durable_records"] = self._total
        enriched["next_shard_index"] = self._next_shard_index
        enriched["writer_state_sha256"] = self._state_digest()
        atomic_write_json(self.checkpoint_path, enriched)

    def finalize(self, checkpoint: Mapping[str, Any]) -> StoreManifest:
        self.checkpoint(checkpoint)
        aggregate = sha256(
            "".join(receipt.sha256 for receipt in self._receipts).encode("ascii")
        ).hexdigest()
        manifest = StoreManifest(
            format="jsonl-sharded-stream-v2",
            records=self._total,
            shards=tuple(self._receipts),
            aggregate_sha256=aggregate,
            checkpoint_path=str(self.checkpoint_path.relative_to(self.root)),
        )
        atomic_write_json(self.manifest_path, manifest.to_dict())
        return manifest

    def verify(self) -> None:
        counted = 0
        for receipt in self._receipts:
            path = self.root / receipt.path
            encoded = path.read_bytes()
            if len(encoded) != receipt.bytes:
                raise ValueError(f"byte-count mismatch for {receipt.path}")
            if sha256(encoded).hexdigest() != receipt.sha256:
                raise ValueError(f"SHA-256 mismatch for {receipt.path}")
            counted += receipt.records
        if counted != self._total:
            raise ValueError("writer-state record count mismatch")

    def _state_payload(self) -> dict[str, Any]:
        return {
            "format": "omega-vla-stream-writer-state-v1",
            "prefix": self.prefix,
            "records_per_shard": self.records_per_shard,
            "total_records": self._total,
            "next_shard_index": self._next_shard_index,
            "shards": [receipt.to_dict() for receipt in self._receipts],
        }

    def _state_digest(self) -> str:
        encoded = json.dumps(
            self._state_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

    def _write_state(self) -> None:
        atomic_write_json(self.state_path, self._state_payload())

    def _load_state(self) -> None:
        if not self.state_path.exists():
            raise FileNotFoundError("resume requested but writer-state.json is absent")
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if payload.get("prefix") != self.prefix:
            raise ValueError("resume prefix does not match persisted writer state")
        if int(payload.get("records_per_shard")) != self.records_per_shard:
            raise ValueError("resume shard size does not match persisted writer state")
        self._receipts = [
            ShardReceipt.from_dict(item) for item in payload.get("shards", [])
        ]
        self._total = int(payload.get("total_records", 0))
        self._next_shard_index = int(payload.get("next_shard_index", 0))
        self.verify()

    def _reset_files(self) -> None:
        for path in self.shard_dir.glob(f"{self.prefix}-*.jsonl"):
            path.unlink()
        for path in (self.checkpoint_path, self.manifest_path, self.state_path):
            if path.exists():
                path.unlink()


class ShardedJSONLStore:
    """Compatibility wrapper for bounded iterable writes."""

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
        writer = StreamingShardedJSONLWriter(
            self.root,
            records_per_shard=self.records_per_shard,
            prefix=self.prefix,
            reset=True,
        )
        writer.extend(records)
        return writer.finalize(checkpoint)

    def read_manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def read_checkpoint(self) -> dict[str, Any]:
        return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
