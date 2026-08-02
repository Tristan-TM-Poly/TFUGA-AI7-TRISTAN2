"""Append-only hash-chained evidence ledger."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .hashing import sha256_object


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    entry_id: str
    event_type: str
    subject_id: str
    payload: dict[str, Any]
    previous_hash: str
    entry_hash: str
    recorded_at: str


class EvidenceLedger:
    GENESIS = "0" * 64

    def __init__(self, entries: Iterable[LedgerEntry] = ()) -> None:
        self.entries = list(entries)

    def append(self, *, entry_id: str, event_type: str, subject_id: str, payload: dict[str, Any]) -> LedgerEntry:
        previous_hash = self.entries[-1].entry_hash if self.entries else self.GENESIS
        record_without_hash = {
            "sequence": len(self.entries),
            "entry_id": entry_id,
            "event_type": event_type,
            "subject_id": subject_id,
            "payload": payload,
            "previous_hash": previous_hash,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        entry = LedgerEntry(entry_hash=sha256_object(record_without_hash), **record_without_hash)
        self.entries.append(entry)
        return entry

    def verify(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        previous = self.GENESIS
        for index, entry in enumerate(self.entries):
            if entry.sequence != index: errors.append(f"sequence:{index}")
            if entry.previous_hash != previous: errors.append(f"previous_hash:{entry.entry_id}")
            payload = asdict(entry)
            claimed = payload.pop("entry_hash")
            if sha256_object(payload) != claimed: errors.append(f"entry_hash:{entry.entry_id}")
            previous = entry.entry_hash
        return (not errors, tuple(errors))

    def write_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for entry in self.entries:
                handle.write(json.dumps(asdict(entry), ensure_ascii=False, sort_keys=True) + "\n")

    @classmethod
    def read_jsonl(cls, path: Path) -> "EvidenceLedger":
        if not path.exists(): return cls()
        return cls(LedgerEntry(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
