from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    assert_no_secret_keys,
    canonical_hash,
    canonical_json,
    ensure_utc,
    is_hmac_sha256,
    is_sha256,
    normalize_text,
    utc_now,
    validate_public_identifier,
)


class EventType(str, Enum):
    COMPANY_IDENTITY_REGISTERED = "company_identity_registered"
    COMPANY_IDENTITY_TRANSITIONED = "company_identity_transitioned"
    AUTHORITY_GRANTED = "authority_granted"
    AUTHORITY_REVOKED = "authority_revoked"
    ORGANIZATION_DISCOVERED = "organization_discovered"
    ORGANIZATION_QUALIFIED = "organization_qualified"
    ORGANIZATION_MERGED = "organization_merged"
    CONTACT_DISCOVERED = "contact_discovered"
    CONTACT_VERIFIED = "contact_verified"
    CONTACT_SUPPRESSED = "contact_suppressed"
    CONSENT_RECORDED = "consent_recorded"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_QUALIFIED = "opportunity_qualified"
    OPPORTUNITY_STATE_CHANGED = "opportunity_state_changed"
    PORTFOLIO_SELECTED = "portfolio_selected"
    MESSAGE_PREPARED = "message_prepared"
    MESSAGE_APPROVED = "message_approved"
    MESSAGE_SENT = "message_sent"
    DELIVERY_RECONCILED = "delivery_reconciled"
    REPLY_RECEIVED = "reply_received"
    REPLY_CLASSIFIED = "reply_classified"
    NEXT_ACTION_SELECTED = "next_action_selected"
    MEETING_CREATED = "meeting_created"
    MEETING_COMPLETED = "meeting_completed"
    PROPOSAL_CREATED = "proposal_created"
    PILOT_CREATED = "pilot_created"
    PILOT_COMPLETED = "pilot_completed"
    CONTRACT_APPROVED = "contract_approved"
    PAYMENT_RECONCILED = "payment_reconciled"
    CASE_CLOSED = "case_closed"
    MMINUS_RECORDED = "mminus_recorded"


class AggregateType(str, Enum):
    COMPANY = "company"
    ORGANIZATION = "organization"
    CONTACT = "contact"
    CONSENT = "consent"
    OPPORTUNITY = "opportunity"
    OUTREACH_CASE = "outreach_case"
    MESSAGE = "message"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    PILOT = "pilot"
    DEAL = "deal"
    PORTFOLIO = "portfolio"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class EventActor:
    actor_id: str
    actor_type: str
    company_id: str | None = None
    authority_hash: str | None = None

    def __post_init__(self) -> None:
        actor_id = normalize_text(self.actor_id).casefold()
        actor_type = normalize_text(self.actor_type).casefold().replace(" ", "_")
        if not actor_id or not actor_type:
            raise CanonicalizationError("event actor_id and actor_type are required")
        if self.authority_hash is not None and not is_sha256(self.authority_hash):
            raise CanonicalizationError("event actor authority_hash must be SHA-256")
        object.__setattr__(self, "actor_id", actor_id)
        object.__setattr__(self, "actor_type", actor_type)
        if self.company_id:
            object.__setattr__(
                self, "company_id", normalize_text(self.company_id).casefold().replace(" ", "_")
            )


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: str
    event_type: EventType
    aggregate_type: AggregateType
    aggregate_id: str
    sequence: int
    occurred_at: datetime
    actor: EventActor
    payload: Mapping[str, Any]
    previous_hash: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            validate_public_identifier(self.event_id, prefix="EVT"),
        )
        if self.sequence < 1:
            raise CanonicalizationError("event sequence must be positive")
        aggregate_id = normalize_text(self.aggregate_id)
        if not aggregate_id:
            raise CanonicalizationError("aggregate_id is required")
        if self.previous_hash is not None and not is_sha256(self.previous_hash):
            raise CanonicalizationError("event previous_hash must be canonical SHA-256")
        if self.correlation_id:
            object.__setattr__(
                self,
                "correlation_id",
                validate_public_identifier(self.correlation_id, prefix="CORR"),
            )
        if self.causation_id:
            object.__setattr__(
                self,
                "causation_id",
                validate_public_identifier(self.causation_id, prefix="EVT"),
            )
        if self.idempotency_key is not None:
            if not (is_sha256(self.idempotency_key) or is_hmac_sha256(self.idempotency_key)):
                raise CanonicalizationError("idempotency_key must be SHA-256 or HMAC-SHA-256")
        if not self.schema_version or len(self.schema_version) > 32:
            raise CanonicalizationError("invalid event schema_version")
        assert_no_secret_keys(self.payload)
        object.__setattr__(self, "aggregate_id", aggregate_id)
        object.__setattr__(self, "occurred_at", ensure_utc(self.occurred_at))
        object.__setattr__(self, "payload", dict(self.payload))

    @property
    def event_hash(self) -> str:
        return canonical_hash(self.unsigned_mapping())

    def unsigned_mapping(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_type": self.aggregate_type.value,
            "aggregate_id": self.aggregate_id,
            "sequence": self.sequence,
            "occurred_at": self.occurred_at,
            "actor": self.actor,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "idempotency_key": self.idempotency_key,
            "schema_version": self.schema_version,
        }

    def stored_mapping(self) -> dict[str, Any]:
        return {**self.unsigned_mapping(), "event_hash": self.event_hash}


@dataclass(frozen=True, slots=True)
class EventAuditResult:
    valid: bool
    event_count: int
    aggregate_count: int
    last_hash: str | None
    errors: tuple[str, ...]

    @property
    def audit_hash(self) -> str:
        return canonical_hash(self)


class EventStore:
    """Append-only JSONL event store with aggregate and global chain checks."""

    def __init__(self, path: Path):
        self.path = path

    def __iter__(self) -> Iterator[DomainEvent]:
        return iter(self.read_all())

    def read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        output: list[dict[str, Any]] = []
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
            output.append(payload)
        return output

    def read_all(self) -> tuple[DomainEvent, ...]:
        return tuple(event_from_mapping(payload) for payload in self.read_raw())

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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            event.stored_mapping(), ensure_ascii=False, sort_keys=True, default=str
        )
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
        occurred_at: datetime | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        idempotency_key: str | None = None,
        schema_version: str = "1.0",
    ) -> DomainEvent:
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

    def events_for(
        self, aggregate_type: AggregateType, aggregate_id: str
    ) -> tuple[DomainEvent, ...]:
        return tuple(
            event
            for event in self.read_all()
            if event.aggregate_type is aggregate_type and event.aggregate_id == aggregate_id
        )

    def find_by_correlation(self, correlation_id: str) -> tuple[DomainEvent, ...]:
        normalized = validate_public_identifier(correlation_id, prefix="CORR")
        return tuple(
            event for event in self.read_all() if event.correlation_id == normalized
        )

    def audit(self) -> EventAuditResult:
        errors: list[str] = []
        raw = self.read_raw()
        events: list[DomainEvent] = []
        seen_event_ids: set[str] = set()
        seen_idempotency: set[str] = set()
        aggregate_last_hash: dict[tuple[AggregateType, str], str | None] = {}
        aggregate_sequence: dict[tuple[AggregateType, str], int] = {}
        last_global_hash: str | None = None
        for index, payload in enumerate(raw, start=1):
            stored_hash = payload.get("event_hash")
            unsigned = {key: value for key, value in payload.items() if key != "event_hash"}
            expected_hash = canonical_hash(unsigned)
            if stored_hash != expected_hash:
                errors.append(f"line {index}: event_hash mismatch")
            try:
                event = event_from_mapping(payload)
            except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"line {index}: cannot parse event: {exc}")
                continue
            events.append(event)
            if event.event_id in seen_event_ids:
                errors.append(f"line {index}: duplicate event_id {event.event_id}")
            seen_event_ids.add(event.event_id)
            if event.idempotency_key:
                if event.idempotency_key in seen_idempotency:
                    errors.append(f"line {index}: duplicate idempotency_key")
                seen_idempotency.add(event.idempotency_key)
            key = (event.aggregate_type, event.aggregate_id)
            expected_sequence = aggregate_sequence.get(key, 0) + 1
            if event.sequence != expected_sequence:
                errors.append(
                    f"line {index}: aggregate sequence expected {expected_sequence}, got {event.sequence}"
                )
            expected_previous = aggregate_last_hash.get(key)
            if event.previous_hash != expected_previous:
                errors.append(f"line {index}: aggregate previous_hash mismatch")
            aggregate_sequence[key] = event.sequence
            aggregate_last_hash[key] = event.event_hash
            last_global_hash = event.event_hash
        return EventAuditResult(
            valid=not errors,
            event_count=len(events),
            aggregate_count=len(aggregate_sequence),
            last_hash=last_global_hash,
            errors=tuple(errors),
        )

    def compact_snapshot(
        self,
        destination: Path,
        projector: Callable[[Sequence[DomainEvent]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        audit = self.audit()
        if not audit.valid:
            raise CanonicalizationError("cannot snapshot an invalid event store")
        events = self.read_all()
        projection = dict(projector(events))
        snapshot = {
            "event_store_hash": canonical_hash([event.stored_mapping() for event in events]),
            "last_event_hash": audit.last_hash,
            "event_count": audit.event_count,
            "aggregate_count": audit.aggregate_count,
            "projection": projection,
            "projection_hash": canonical_hash(projection),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(destination, json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2))
        return snapshot


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
    temporary.replace(path)


def event_from_mapping(payload: Mapping[str, Any]) -> DomainEvent:
    actor_payload = payload["actor"]
    if not isinstance(actor_payload, Mapping):
        raise CanonicalizationError("event actor must be an object")
    actor = EventActor(
        actor_id=str(actor_payload["actor_id"]),
        actor_type=str(actor_payload["actor_type"]),
        company_id=actor_payload.get("company_id"),
        authority_hash=actor_payload.get("authority_hash"),
    )
    occurred_at_raw = payload["occurred_at"]
    if isinstance(occurred_at_raw, datetime):
        occurred_at = occurred_at_raw
    else:
        occurred_at = datetime.fromisoformat(str(occurred_at_raw).replace("Z", "+00:00"))
    event = DomainEvent(
        event_id=str(payload["event_id"]),
        event_type=EventType(str(payload["event_type"])),
        aggregate_type=AggregateType(str(payload["aggregate_type"])),
        aggregate_id=str(payload["aggregate_id"]),
        sequence=int(payload["sequence"]),
        occurred_at=occurred_at,
        actor=actor,
        payload=dict(payload["payload"]),
        previous_hash=payload.get("previous_hash"),
        correlation_id=payload.get("correlation_id"),
        causation_id=payload.get("causation_id"),
        idempotency_key=payload.get("idempotency_key"),
        schema_version=str(payload.get("schema_version", "1.0")),
    )
    stored_hash = payload.get("event_hash")
    if stored_hash is not None and stored_hash != event.event_hash:
        raise CanonicalizationError("stored event hash does not match canonical event")
    return event


@dataclass(frozen=True, slots=True)
class OutreachProjection:
    companies: Mapping[str, Mapping[str, Any]]
    organizations: Mapping[str, Mapping[str, Any]]
    contacts: Mapping[str, Mapping[str, Any]]
    opportunities: Mapping[str, Mapping[str, Any]]
    cases: Mapping[str, Mapping[str, Any]]
    metrics: Mapping[str, int | float]

    @property
    def projection_hash(self) -> str:
        return canonical_hash(self)


def build_outreach_projection(events: Sequence[DomainEvent]) -> OutreachProjection:
    companies: dict[str, dict[str, Any]] = {}
    organizations: dict[str, dict[str, Any]] = {}
    contacts: dict[str, dict[str, Any]] = {}
    opportunities: dict[str, dict[str, Any]] = {}
    cases: dict[str, dict[str, Any]] = {}
    metrics: dict[str, int | float] = {
        "events": 0,
        "messages_sent": 0,
        "replies_received": 0,
        "meetings_created": 0,
        "pilots_created": 0,
        "payments_reconciled": 0,
    }
    for event in events:
        metrics["events"] = int(metrics["events"]) + 1
        target: dict[str, dict[str, Any]] | None = None
        if event.aggregate_type is AggregateType.COMPANY:
            target = companies
        elif event.aggregate_type is AggregateType.ORGANIZATION:
            target = organizations
        elif event.aggregate_type is AggregateType.CONTACT:
            target = contacts
        elif event.aggregate_type is AggregateType.OPPORTUNITY:
            target = opportunities
        elif event.aggregate_type is AggregateType.OUTREACH_CASE:
            target = cases
        if target is not None:
            current = dict(target.get(event.aggregate_id, {}))
            current.update(
                {
                    "aggregate_id": event.aggregate_id,
                    "last_event_type": event.event_type.value,
                    "last_event_hash": event.event_hash,
                    "last_occurred_at": event.occurred_at,
                    "sequence": event.sequence,
                }
            )
            public_patch = event.payload.get("projection")
            if isinstance(public_patch, Mapping):
                current.update(public_patch)
            target[event.aggregate_id] = current
        if event.event_type is EventType.MESSAGE_SENT:
            metrics["messages_sent"] = int(metrics["messages_sent"]) + 1
        elif event.event_type is EventType.REPLY_RECEIVED:
            metrics["replies_received"] = int(metrics["replies_received"]) + 1
        elif event.event_type is EventType.MEETING_CREATED:
            metrics["meetings_created"] = int(metrics["meetings_created"]) + 1
        elif event.event_type is EventType.PILOT_CREATED:
            metrics["pilots_created"] = int(metrics["pilots_created"]) + 1
        elif event.event_type is EventType.PAYMENT_RECONCILED:
            metrics["payments_reconciled"] = int(metrics["payments_reconciled"]) + 1
    return OutreachProjection(
        companies=dict(sorted(companies.items())),
        organizations=dict(sorted(organizations.items())),
        contacts=dict(sorted(contacts.items())),
        opportunities=dict(sorted(opportunities.items())),
        cases=dict(sorted(cases.items())),
        metrics=dict(sorted(metrics.items())),
    )


def replay(
    events: Iterable[DomainEvent],
    reducer: Callable[[Any, DomainEvent], Any],
    initial: Any,
) -> Any:
    state = initial
    for event in events:
        state = reducer(state, event)
    return state


def audit_event_sequence(events: Sequence[DomainEvent]) -> list[str]:
    errors: list[str] = []
    event_ids: set[str] = set()
    idempotency_keys: set[str] = set()
    aggregate_sequences: dict[tuple[AggregateType, str], int] = {}
    aggregate_hashes: dict[tuple[AggregateType, str], str | None] = {}
    for index, event in enumerate(events, start=1):
        if event.event_id in event_ids:
            errors.append(f"event {index}: duplicate event_id {event.event_id}")
        event_ids.add(event.event_id)
        if event.idempotency_key:
            if event.idempotency_key in idempotency_keys:
                errors.append(f"event {index}: duplicate idempotency key")
            idempotency_keys.add(event.idempotency_key)
        key = (event.aggregate_type, event.aggregate_id)
        expected_sequence = aggregate_sequences.get(key, 0) + 1
        if event.sequence != expected_sequence:
            errors.append(
                f"event {index}: expected aggregate sequence {expected_sequence}, got {event.sequence}"
            )
        if event.previous_hash != aggregate_hashes.get(key):
            errors.append(f"event {index}: aggregate previous hash mismatch")
        aggregate_sequences[key] = event.sequence
        aggregate_hashes[key] = event.event_hash
        if event.causation_id and event.causation_id not in event_ids:
            errors.append(f"event {index}: causation event has not occurred yet")
    return errors
