from __future__ import annotations

"""Disk-backed, checkpointed campaign runner without a permanent item ceiling."""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class CampaignBudget:
    max_seconds: float | None = None
    max_output_bytes: int | None = None
    max_failures: int | None = None
    minimum_quality: float = 0.0
    checkpoint_every: int = 1000
    shard_target_bytes: int = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class CampaignState:
    accepted: int
    duplicates: int
    rejected: int
    failures: int
    output_bytes: int
    shards: int
    stop_reason: str
    elapsed_seconds: float
    last_sequence: int


class CampaignRunner:
    def __init__(self, root: str | Path, budget: CampaignBudget | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.budget = budget or CampaignBudget()
        self.database = sqlite3.connect(self.root / "index.sqlite3")
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS seen (fingerprint TEXT PRIMARY KEY, sequence INTEGER, shard TEXT)"
        )
        self.database.commit()

    def close(self) -> None:
        self.database.close()

    def run(
        self,
        source: Iterable[Mapping[str, Any]],
        *,
        fingerprint: Callable[[Mapping[str, Any]], str] | None = None,
        quality: Callable[[Mapping[str, Any]], float] | None = None,
    ) -> CampaignState:
        start = time.monotonic()
        accepted = duplicates = rejected = failures = output_bytes = 0
        sequence = -1
        shard_index = self._next_shard_index()
        shard_path = self.root / f"shard-{shard_index:06d}.jsonl"
        shard_handle = shard_path.open("a", encoding="utf-8")
        shard_bytes = shard_path.stat().st_size if shard_path.exists() else 0
        stop_reason = "source_exhausted"
        try:
            for sequence, item in enumerate(source):
                reason = self._budget_stop(start, output_bytes, failures)
                if reason is not None:
                    stop_reason = reason
                    break
                try:
                    item_quality = 1.0 if quality is None else float(quality(item))
                    if item_quality < self.budget.minimum_quality:
                        rejected += 1
                        continue
                    serialized = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                    digest = (
                        fingerprint(item)
                        if fingerprint is not None
                        else sha256(serialized.encode("utf-8")).hexdigest()
                    )
                    try:
                        self.database.execute(
                            "INSERT INTO seen(fingerprint, sequence, shard) VALUES (?, ?, ?)",
                            (digest, sequence, shard_path.name),
                        )
                    except sqlite3.IntegrityError:
                        duplicates += 1
                        continue
                    encoded = serialized + "\n"
                    encoded_bytes = len(encoded.encode("utf-8"))
                    if shard_bytes and shard_bytes + encoded_bytes > self.budget.shard_target_bytes:
                        shard_handle.close()
                        self.database.commit()
                        shard_index += 1
                        shard_path = self.root / f"shard-{shard_index:06d}.jsonl"
                        shard_handle = shard_path.open("a", encoding="utf-8")
                        shard_bytes = 0
                    shard_handle.write(encoded)
                    shard_bytes += encoded_bytes
                    output_bytes += encoded_bytes
                    accepted += 1
                    if accepted % self.budget.checkpoint_every == 0:
                        shard_handle.flush()
                        self.database.commit()
                        self._write_checkpoint(
                            accepted,
                            duplicates,
                            rejected,
                            failures,
                            output_bytes,
                            shard_index + 1,
                            "running",
                            time.monotonic() - start,
                            sequence,
                        )
                except Exception as error:  # campaign failure isolation is intentional
                    failures += 1
                    self._append_mminus(sequence, item, error)
            self.database.commit()
        finally:
            shard_handle.close()
        state = CampaignState(
            accepted=accepted,
            duplicates=duplicates,
            rejected=rejected,
            failures=failures,
            output_bytes=output_bytes,
            shards=shard_index + 1,
            stop_reason=stop_reason,
            elapsed_seconds=time.monotonic() - start,
            last_sequence=sequence,
        )
        self._write_state(state)
        return state

    def _budget_stop(self, start: float, output_bytes: int, failures: int) -> str | None:
        if self.budget.max_seconds is not None and time.monotonic() - start >= self.budget.max_seconds:
            return "time_budget"
        if self.budget.max_output_bytes is not None and output_bytes >= self.budget.max_output_bytes:
            return "byte_budget"
        if self.budget.max_failures is not None and failures >= self.budget.max_failures:
            return "failure_budget"
        return None

    def _next_shard_index(self) -> int:
        existing = sorted(self.root.glob("shard-*.jsonl"))
        if not existing:
            return 0
        return int(existing[-1].stem.split("-")[-1]) + 1

    def _append_mminus(self, sequence: int, item: Mapping[str, Any], error: Exception) -> None:
        payload = {
            "sequence": sequence,
            "error_type": type(error).__name__,
            "error": str(error),
            "item": item,
        }
        with (self.root / "m_minus.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")

    def _write_checkpoint(
        self,
        accepted: int,
        duplicates: int,
        rejected: int,
        failures: int,
        output_bytes: int,
        shards: int,
        stop_reason: str,
        elapsed_seconds: float,
        last_sequence: int,
    ) -> None:
        self._write_state(
            CampaignState(
                accepted,
                duplicates,
                rejected,
                failures,
                output_bytes,
                shards,
                stop_reason,
                elapsed_seconds,
                last_sequence,
            )
        )

    def _write_state(self, state: CampaignState) -> None:
        temporary = self.root / "checkpoint.json.tmp"
        temporary.write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.root / "checkpoint.json")
