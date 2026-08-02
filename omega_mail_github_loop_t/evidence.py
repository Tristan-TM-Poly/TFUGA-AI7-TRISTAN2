"""Append-only evidence hash chain."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import EvidenceEvent


class EvidenceLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _head(self) -> str | None:
        if not self.path.exists():
            return None
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return json.loads(lines[-1])["event_hash"] if lines else None

    def append(self, case_id: str, kind: str, payload: dict[str, Any]) -> EvidenceEvent:
        previous = self._head()
        created_at = datetime.now(timezone.utc).isoformat()
        payload_hash = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        material = f"{case_id}|{kind}|{payload_hash}|{previous or ''}|{created_at}"
        event = EvidenceEvent(
            event_id=f"EV-{uuid4().hex[:12]}",
            case_id=case_id,
            kind=kind,
            payload_hash=payload_hash,
            previous_hash=previous,
            event_hash=sha256(material.encode("utf-8")).hexdigest(),
            created_at=created_at,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event

    def verify(self) -> tuple[bool, tuple[str, ...]]:
        if not self.path.exists():
            return True, ("empty_ledger",)
        previous: str | None = None
        errors: list[str] = []
        for index, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("previous_hash") != previous:
                errors.append(f"broken_previous_hash:{index}")
            material = f"{record['case_id']}|{record['kind']}|{record['payload_hash']}|{record.get('previous_hash') or ''}|{record['created_at']}"
            if record.get("event_hash") != sha256(material.encode("utf-8")).hexdigest():
                errors.append(f"invalid_event_hash:{index}")
            previous = record.get("event_hash")
        return not errors, tuple(errors) or ("ledger_verified",)
