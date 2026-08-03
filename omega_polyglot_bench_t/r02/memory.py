"""Append-only positive/negative memory ledger."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    kind: str
    subject_id: str
    code: str
    evidence: dict[str, Any]
    schema_version: str = "omega.polyglot-memory.v2"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        payload["event_id"] = "mem_" + sha256(encoded).hexdigest()[:24]
        return payload


class MemoryLedger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: MemoryEvent) -> str:
        if event.kind not in {"M+", "M-"}:
            raise ValueError("kind must be M+ or M-")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = event.to_dict()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return str(payload["event_id"])

    def read(self) -> tuple[dict[str, Any], ...]:
        if not self.path.exists():
            return ()
        return tuple(json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line)
