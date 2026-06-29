from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    source_type: str
    url: str
    title: str | None = None
    author: str | None = None
    license_id: str | None = None
    revision: str | None = None
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    oak_status: str = "pending"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


class ProvenanceLedger:
    """Append-only JSONL provenance ledger."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: ProvenanceRecord) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json() + "\n")

    def records(self) -> list[ProvenanceRecord]:
        if not self.path.exists():
            return []
        out: list[ProvenanceRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            out.append(ProvenanceRecord(**data))
        return out
