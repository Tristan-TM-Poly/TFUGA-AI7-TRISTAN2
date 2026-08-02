"""Append-only evidence ledger and anti-replay reservation for external actions."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

from .models import ExternalActionEnvelope, canonicalize


GENESIS_HASH = "sha256:" + "0" * 64
_EXECUTION_EVENTS = frozenset({"RESERVED", "EXECUTION_STARTED", "PROVIDER_ACCEPTED", "EFFECT_CONFIRMED", "RECONCILED"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_mapping(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(canonicalize(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    occurred_at: str
    action_id: str
    action_hash: str
    action_type: str
    company_hash: str
    event: str
    provider: str | None
    provider_result_hash: str | None
    previous_hash: str
    entry_hash: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "LedgerEntry":
        return cls(
            sequence=int(data["sequence"]),
            occurred_at=str(data["occurred_at"]),
            action_id=str(data["action_id"]),
            action_hash=str(data["action_hash"]),
            action_type=str(data["action_type"]),
            company_hash=str(data["company_hash"]),
            event=str(data["event"]),
            provider=str(data["provider"]) if data.get("provider") is not None else None,
            provider_result_hash=(
                str(data["provider_result_hash"]) if data.get("provider_result_hash") is not None else None
            ),
            previous_hash=str(data["previous_hash"]),
            entry_hash=str(data["entry_hash"]),
        )

    def unsigned_mapping(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("entry_hash")
        return data

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


class ActionLedger:
    """JSONL hash chain storing hashes and bounded operational events only."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def entries(self) -> tuple[LedgerEntry, ...]:
        if not self.path.exists():
            return ()
        result: list[LedgerEntry] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid ledger JSON at line {line_number}") from exc
            result.append(LedgerEntry.from_mapping(payload))
        return tuple(result)

    def audit(self) -> dict[str, Any]:
        entries = self.entries()
        previous = GENESIS_HASH
        errors: list[str] = []
        for expected, entry in enumerate(entries, 1):
            if entry.sequence != expected:
                errors.append(f"sequence_mismatch:{expected}")
            if entry.previous_hash != previous:
                errors.append(f"previous_hash_mismatch:{expected}")
            calculated = _hash_mapping(entry.unsigned_mapping())
            if entry.entry_hash != calculated:
                errors.append(f"entry_hash_mismatch:{expected}")
            previous = entry.entry_hash
        return {
            "valid": not errors,
            "entries": len(entries),
            "head_hash": previous,
            "errors": errors,
        }

    def has_execution(self, action_hash: str) -> bool:
        return any(entry.action_hash == action_hash and entry.event in _EXECUTION_EVENTS for entry in self.entries())

    def append(
        self,
        action: ExternalActionEnvelope,
        *,
        event: str,
        provider: str | None = None,
        provider_result: Mapping[str, Any] | None = None,
    ) -> LedgerEntry:
        audit = self.audit()
        if not audit["valid"]:
            raise RuntimeError("ledger audit failed; refusing append")
        current = self.entries()
        unsigned = {
            "sequence": len(current) + 1,
            "occurred_at": _now(),
            "action_id": action.action_id,
            "action_hash": action.action_hash,
            "action_type": action.action_type.value,
            "company_hash": _hash_mapping({"company_id": action.company_id}),
            "event": event,
            "provider": provider,
            "provider_result_hash": _hash_mapping(provider_result) if provider_result is not None else None,
            "previous_hash": audit["head_hash"],
        }
        entry = LedgerEntry(entry_hash=_hash_mapping(unsigned), **unsigned)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_mapping(), sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return entry

    def reserve(self, action: ExternalActionEnvelope, *, provider: str) -> LedgerEntry:
        with self.exclusive_lock():
            if self.has_execution(action.action_hash):
                raise RuntimeError("action replay blocked")
            return self.append(action, event="RESERVED", provider=provider)

    @contextmanager
    def exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError("action ledger is locked; manual review required for stale locks") from exc
        try:
            os.write(descriptor, f"pid={os.getpid()}\n".encode("utf-8"))
            os.close(descriptor)
            yield
        finally:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
