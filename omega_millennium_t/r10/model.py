from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

CELL_SCHEMA = "omega-problem-stream-cell/10"
REPORT_SCHEMA = "omega-problem-stream-report/10"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_digest(value: Any) -> str:
    return sha256_text(canonical_json(value))


def require_nonempty(value: Any, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{field_name} must be non-empty")
    return result


@dataclass(frozen=True)
class CellRecord:
    cell_id: str
    problem_id: str
    target_id: str
    front: str
    method: str
    priority: int
    source_ref: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "CellRecord":
        allowed = {
            "schema",
            "cell_id",
            "problem_id",
            "target_id",
            "front",
            "method",
            "priority",
            "source_ref",
            "payload",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown cell fields: {sorted(unknown)}")
        if row.get("schema") != CELL_SCHEMA:
            raise ValueError(f"schema must equal {CELL_SCHEMA}")
        priority = row.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError("priority must be an integer")
        payload = row.get("payload", {})
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be an object")
        return cls(
            cell_id=require_nonempty(row.get("cell_id"), "cell_id"),
            problem_id=require_nonempty(row.get("problem_id"), "problem_id"),
            target_id=require_nonempty(row.get("target_id"), "target_id"),
            front=require_nonempty(row.get("front"), "front"),
            method=require_nonempty(row.get("method"), "method"),
            priority=priority,
            source_ref=require_nonempty(row.get("source_ref"), "source_ref"),
            payload=dict(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CELL_SCHEMA,
            "cell_id": self.cell_id,
            "problem_id": self.problem_id,
            "target_id": self.target_id,
            "front": self.front,
            "method": self.method,
            "priority": self.priority,
            "source_ref": self.source_ref,
            "payload": dict(self.payload),
        }

    @property
    def digest(self) -> str:
        return stable_digest(self.to_dict())


@dataclass(frozen=True)
class RuntimePolicy:
    batch_size: int = 1000
    shard_target_bytes: int = 8 * 1024 * 1024
    max_disk_bytes: int | None = None
    sqlite_busy_timeout_ms: int = 30_000

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.shard_target_bytes < 1024:
            raise ValueError("shard_target_bytes must be >= 1024")
        if self.max_disk_bytes is not None and self.max_disk_bytes < 1:
            raise ValueError("max_disk_bytes must be positive when supplied")
        if self.sqlite_busy_timeout_ms < 1:
            raise ValueError("sqlite_busy_timeout_ms must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "shard_target_bytes": self.shard_target_bytes,
            "max_disk_bytes": self.max_disk_bytes,
            "sqlite_busy_timeout_ms": self.sqlite_busy_timeout_ms,
            "permanent_total_cell_cap": None,
        }


class MerkleAccumulator:
    """Streaming binary Merkle accumulator using deterministic peak folding."""

    def __init__(self, peaks: list[str | None] | None = None, leaf_count: int = 0) -> None:
        self.peaks = list(peaks or [])
        self.leaf_count = int(leaf_count)

    @staticmethod
    def _combine(left: str, right: str) -> str:
        return sha256_text(f"node:{left}:{right}")

    def add_digest(self, digest: str) -> None:
        carry = sha256_text(f"leaf:{digest}")
        level = 0
        while True:
            if level >= len(self.peaks):
                self.peaks.append(carry)
                break
            current = self.peaks[level]
            if current is None:
                self.peaks[level] = carry
                break
            carry = self._combine(current, carry)
            self.peaks[level] = None
            level += 1
        self.leaf_count += 1

    def root(self) -> str:
        active = [item for item in self.peaks if item is not None]
        if not active:
            return sha256_text("empty-merkle")
        result = active[-1]
        for item in reversed(active[:-1]):
            result = self._combine(item, result)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "peaks": self.peaks,
            "leaf_count": self.leaf_count,
            "root": self.root(),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MerkleAccumulator":
        peaks = value.get("peaks", [])
        if not isinstance(peaks, list) or any(
            item is not None and not isinstance(item, str) for item in peaks
        ):
            raise ValueError("invalid Merkle peaks")
        leaf_count = value.get("leaf_count", 0)
        if not isinstance(leaf_count, int) or leaf_count < 0:
            raise ValueError("invalid Merkle leaf_count")
        instance = cls(list(peaks), leaf_count)
        expected = value.get("root")
        if expected is not None and expected != instance.root():
            raise ValueError("Merkle checkpoint root mismatch")
        return instance


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_jsonl(path: Path, *, start_line: int = 1) -> Iterable[tuple[int, dict[str, Any], str]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if line_number < start_line:
                continue
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed_jsonl:{line_number}:{exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"jsonl_row_not_object:{line_number}")
            yield line_number, value, raw_line
