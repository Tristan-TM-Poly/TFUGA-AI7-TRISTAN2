"""Append-only SHA-256 evidence ledger with hash-chain verification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

GENESIS = "0" * 64


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    previous_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_event_hash(sequence: int, event_type: str, payload: Mapping[str, Any], previous_hash: str) -> str:
    material = {"sequence": sequence, "event_type": event_type, "payload": payload, "previous_hash": previous_hash}
    return hashlib.sha256(_canonical(material)).hexdigest()


def build_event(sequence: int, event_type: str, payload: Mapping[str, Any], previous_hash: str) -> LedgerEvent:
    if sequence < 0 or not event_type:
        raise ValueError("invalid ledger event")
    if len(previous_hash) != 64:
        raise ValueError("previous_hash must be a SHA-256 hex digest")
    event_hash = compute_event_hash(sequence, event_type, payload, previous_hash)
    return LedgerEvent(sequence, event_type, dict(payload), previous_hash, event_hash)


def verify_events(events: Iterable[LedgerEvent]) -> dict[str, object]:
    previous = GENESIS
    expected_sequence = 0
    errors: list[str] = []
    count = 0
    for event in events:
        if event.sequence != expected_sequence:
            errors.append(f"sequence:{event.sequence}!={expected_sequence}")
        if event.previous_hash != previous:
            errors.append(f"previous_hash_mismatch:{event.sequence}")
        expected_hash = compute_event_hash(event.sequence, event.event_type, event.payload, event.previous_hash)
        if event.event_hash != expected_hash:
            errors.append(f"event_hash_mismatch:{event.sequence}")
        previous = event.event_hash
        expected_sequence += 1
        count += 1
    return {"valid": not errors, "events": count, "head": previous, "errors": errors}


def append_event(path: Path, event_type: str, payload: Mapping[str, Any]) -> LedgerEvent:
    events = list(read_events(path)) if path.exists() else []
    audit = verify_events(events)
    if not audit["valid"]:
        raise ValueError(f"ledger is invalid: {audit['errors']}")
    previous = str(audit["head"])
    event = build_event(len(events), event_type, payload, previous)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    return event


def read_events(path: Path) -> Iterable[LedgerEvent]:
    if not path.exists():
        return ()
    def iterator() -> Iterable[LedgerEvent]:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                raw = json.loads(line)
                yield LedgerEvent(
                    sequence=int(raw["sequence"]),
                    event_type=str(raw["event_type"]),
                    payload=dict(raw["payload"]),
                    previous_hash=str(raw["previous_hash"]),
                    event_hash=str(raw["event_hash"]),
                )
    return iterator()
