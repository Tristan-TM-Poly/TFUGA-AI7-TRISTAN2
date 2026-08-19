"""Append-only local ledger for manifests and proofs.

This module writes JSONL records to a caller-provided path. It does not contact
external services and is safe for dry-run testing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LedgerRecord:
    kind: str
    payload: dict[str, Any]
    timestamp: str
    previous_hash: str | None
    record_hash: str


class ProofLedger:
    """Minimal append-only JSONL ledger.

    The hash chain gives a tamper-evident local trail. Future versions can anchor
    selected hashes in Git commits, signed artifacts, or private storage.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, kind: str, payload: dict[str, Any]) -> LedgerRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        previous_hash = self.latest_hash()
        timestamp = datetime.now(timezone.utc).isoformat()
        record_hash = self._hash(kind, payload, timestamp, previous_hash)
        record = LedgerRecord(kind, payload, timestamp, previous_hash, record_hash)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.__dict__, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def latest_hash(self) -> str | None:
        if not self.path.exists():
            return None
        last = None
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = json.loads(line)
        return None if last is None else str(last.get("record_hash"))

    def records(self) -> list[LedgerRecord]:
        if not self.path.exists():
            return []
        out: list[LedgerRecord] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(LedgerRecord(**json.loads(line)))
        return out

    @staticmethod
    def _hash(kind: str, payload: dict[str, Any], timestamp: str, previous_hash: str | None) -> str:
        data = {
            "kind": kind,
            "payload": payload,
            "timestamp": timestamp,
            "previous_hash": previous_hash,
        }
        encoded = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + sha256(encoded).hexdigest()
