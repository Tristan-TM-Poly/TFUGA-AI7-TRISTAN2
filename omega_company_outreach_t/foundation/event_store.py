from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterator, Mapping, Sequence

from .canonical import CanonicalizationError, canonical_hash, canonical_mapping
from .events import (
    AggregateType,
    DomainEvent,
    EventActor,
    EventAuditResult,
    EventType,
    event_from_mapping,
)


class CanonicalEventStore:
    """Canonical JSONL runtime for DomainEvent.

    The original R1.0 model module defines the event vocabulary and projections.
    This runtime owns persistence so that datetime and dataclass values are always
    serialized through canonical_mapping before hashes are re-evaluated.
    """

    def __init__(self, path: Path):
        self.path = path

    def __iter__(self) -> Iterator[DomainEvent]:
        return iter(self.read_all())

    def read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CanonicalizationError(
                    f"event store line {line_number} is invalid JSON: {exc}"
                ) from exc
            if not isinstance(payload, dict):
                raise CanonicalizationError(
                    f"event store line {line_number} must be a JSON object"
                )
            rows.append(payload)
        return rows

    def read_all(self) -> tuple[DomainEvent, ...]:
        return tuple(event_from_mapping(payload) for payload in self.read_raw())

    def events_for(
        self, aggregate_type: AggregateType, aggregate_id: str
    ) -> tuple[DomainEvent, ...]:
        return tuple(
            event
            for event in self.read_all()
            if event.aggregate_type is aggregate_type and event.aggregate_id == aggregate_id
        )

    def append(self, event: DomainEvent) -> DomainEvent:
        audit = self.audit()
        if not audit.valid:
            raise CanonicalizationError("cannot append to an invalid event store")
        events = self.read_all()
        if any(existing.event_id == event.event_id for existing in events):
            raise CanonicalizationError(f"event_id already exists: {event.event_id}")
        if event.idempotency_key and any(
            existing.idempotency_key == event.idempotency_key for existing in events
        ):
            raise CanonicalizationError("idempotency_key has already been consumed")
        aggregate_events = [
            existing
            for existing in events
            if existing.aggregate_type is event.aggregate_type
            and existing.aggregate_id == event.aggregate_id
        ]
        expected_sequence = len(aggregate_events) + 1
        if event.sequence != expected_sequence:
            raise CanonicalizationError(
                f"event sequence must be {expected_sequence} for aggregate, got {event.sequence}"
            )
        expected_previous = aggregate_events[-1].event_hash if aggregate_events else None
        if event.previous_hash != expected_previous:
            raise CanonicalizationError("event previous_hash does not match aggregate chain")
        row = canonical_mapping(event.stored_mapping())
        line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
        return event

    def append_new(
        self,
        *,
        event_id: str,
        event_type: EventType,
        aggregate_type: AggregateType,
        aggregate_id: str,
        actor: EventActor,
        payload: Mapping[str, Any],
        occurred_at=None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        idempotency_key: str | None = None,
        schema_version: str = "1.0",
    ) -> DomainEvent:
        from .canonical import utc_now

        aggregate_events = self.events_for(aggregate_type, aggregate_id)
        event = DomainEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            sequence=len(aggregate_events) + 1,
            occurred_at=occurred_at or utc_now(),
            actor=actor,
            payload=payload,
            previous_hash=aggregate_events[-1].event_hash if aggregate_events else None,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            schema_version=schema_version,
        )
        return self.append(event)

    def audit(self) -> EventAuditResult:
        rows = self.read_raw()
        errors: list[str] = []
        event_ids: set[str] = set()
        idempotency_keys: set[str] = set()
        aggregate_last_hash: dict[tuple[AggregateType, str], str | None] = {}
        aggregate_sequence: dict[tuple[AggregateType, str], int] = {}
        last_hash: str | None = None
        parsed_count = 0
        for line_number, row in enumerate(rows, start=1):
            stored_hash = row.get("event_hash")
            unsigned = {key: value for key, value in row.items() if key != "event_hash"}
            if stored_hash != canonical_hash(unsigned):
                errors.append(f"line {line_number}: event_hash mismatch")
            try:
                event = event_from_mapping(row)
            except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"line {line_number}: cannot parse event: {exc}")
                continue
            parsed_count += 1
            if event.event_id in event_ids:
                errors.append(f"line {line_number}: duplicate event_id {event.event_id}")
            event_ids.add(event.event_id)
            if event.idempotency_key:
                if event.idempotency_key in idempotency_keys:
                    errors.append(f"line {line_number}: duplicate idempotency_key")
                idempotency_keys.add(event.idempotency_key)
            key = (event.aggregate_type, event.aggregate_id)
            expected_sequence = aggregate_sequence.get(key, 0) + 1
            if event.sequence != expected_sequence:
                errors.append(
                    f"line {line_number}: aggregate sequence expected {expected_sequence}, "
                    f"got {event.sequence}"
                )
            if event.previous_hash != aggregate_last_hash.get(key):
                errors.append(f"line {line_number}: aggregate previous_hash mismatch")
            aggregate_sequence[key] = event.sequence
            aggregate_last_hash[key] = event.event_hash
            last_hash = event.event_hash
        return EventAuditResult(
            valid=not errors,
            event_count=parsed_count,
            aggregate_count=len(aggregate_sequence),
            last_hash=last_hash,
            errors=tuple(errors),
        )

    def write_snapshot(
        self,
        destination: Path,
        projector: Callable[[Sequence[DomainEvent]], Any],
    ) -> dict[str, Any]:
        audit = self.audit()
        if not audit.valid:
            raise CanonicalizationError("cannot snapshot an invalid event store")
        events = self.read_all()
        projection = projector(events)
        payload = canonical_mapping(
            {
                "event_count": audit.event_count,
                "aggregate_count": audit.aggregate_count,
                "last_event_hash": audit.last_hash,
                "event_store_hash": canonical_hash([event.stored_mapping() for event in events]),
                "projection": projection,
                "projection_hash": canonical_hash(projection),
            }
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(
            destination,
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        )
        return payload


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
    temporary.replace(path)
