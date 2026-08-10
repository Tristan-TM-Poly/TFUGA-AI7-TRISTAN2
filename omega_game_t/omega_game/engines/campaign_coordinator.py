from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable

from .campaign import CampaignManifest
from .campaign_bundle import TTLLeaseCoordinator, WorkerManifest, WorkerRegistry


COORDINATOR_EVENT_VERSION = "0.1"
EVENT_KINDS = {
    "worker_registered",
    "worker_heartbeat",
    "shard_assigned",
    "shard_acknowledged",
    "shard_succeeded",
    "shard_failed",
    "lease_expired",
    "retry_scheduled",
}
TERMINAL_SHARD_STATES = {"succeeded", "exhausted"}


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class CoordinatorEvent:
    version: str
    sequence: int
    kind: str
    plan_receipt: str
    previous_receipt: str | None
    shard_id: int | None
    worker_id: str | None
    attempt: int | None
    payload: dict[str, Any]
    event_receipt: str

    def body(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "sequence": self.sequence,
            "kind": self.kind,
            "plan_receipt": self.plan_receipt,
            "previous_receipt": self.previous_receipt,
            "shard_id": self.shard_id,
            "worker_id": self.worker_id,
            "attempt": self.attempt,
            "payload": self.payload,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "event_receipt": self.event_receipt}


@dataclass
class CoordinatorLedger:
    plan_receipt: str
    events: list[CoordinatorEvent] = field(default_factory=list)

    @property
    def head_receipt(self) -> str | None:
        return None if not self.events else self.events[-1].event_receipt

    def append(
        self,
        kind: str,
        *,
        shard_id: int | None = None,
        worker_id: str | None = None,
        attempt: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CoordinatorEvent:
        if kind not in EVENT_KINDS:
            raise ValueError(f"unsupported coordinator event kind: {kind}")
        body = {
            "version": COORDINATOR_EVENT_VERSION,
            "sequence": len(self.events) + 1,
            "kind": kind,
            "plan_receipt": self.plan_receipt,
            "previous_receipt": self.head_receipt,
            "shard_id": shard_id,
            "worker_id": worker_id,
            "attempt": attempt,
            "payload": dict(payload or {}),
        }
        event = CoordinatorEvent(**body, event_receipt=_canonical_hash(body))
        self.events.append(event)
        return event

    def validate_chain(self) -> None:
        previous: str | None = None
        for index, event in enumerate(self.events, start=1):
            if event.version != COORDINATOR_EVENT_VERSION:
                raise ValueError("unsupported coordinator event version")
            if event.sequence != index:
                raise ValueError("coordinator event sequence mismatch")
            if event.kind not in EVENT_KINDS:
                raise ValueError("unknown coordinator event kind")
            if event.plan_receipt != self.plan_receipt:
                raise ValueError("coordinator event plan mismatch")
            if event.previous_receipt != previous:
                raise ValueError("coordinator event causal link mismatch")
            if _canonical_hash(event.body()) != event.event_receipt:
                raise ValueError("coordinator event receipt mismatch")
            previous = event.event_receipt

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_receipt": self.plan_receipt,
            "event_count": len(self.events),
            "head_receipt": self.head_receipt,
            "events": [event.to_dict() for event in self.events],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


@dataclass
class ShardCoordinatorState:
    shard_id: int
    status: str = "pending"
    attempt: int = 0
    worker_id: str | None = None
    lease_token: str | None = None
    checkpoint_receipt: str | None = None
    failure_receipt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoordinatorAudit:
    accepted: bool
    flags: tuple[str, ...]
    head_receipt: str | None
    shard_states: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "flags": list(self.flags),
            "head_receipt": self.head_receipt,
            "shard_states": list(self.shard_states),
        }


@dataclass
class CampaignCoordinator:
    manifest: CampaignManifest
    max_attempts: int = 2
    clock: Callable[[], float] = time.monotonic
    ledger: CoordinatorLedger = field(init=False)
    registry: WorkerRegistry = field(init=False)
    leases: TTLLeaseCoordinator = field(init=False)
    shard_states: dict[int, ShardCoordinatorState] = field(init=False)

    def __post_init__(self) -> None:
        self.manifest.validate()
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.ledger = CoordinatorLedger(self.manifest.plan_receipt)
        self.registry = WorkerRegistry(clock=self.clock)
        self.leases = TTLLeaseCoordinator(self.manifest.plan_receipt, self.registry, clock=self.clock)
        self.shard_states = {
            shard.shard_id: ShardCoordinatorState(shard.shard_id)
            for shard in self.manifest.shards
        }

    def register_worker(self, manifest: WorkerManifest) -> CoordinatorEvent:
        self.registry.register(manifest)
        return self.ledger.append(
            "worker_registered",
            worker_id=manifest.worker_id,
            payload={"manifest_receipt": manifest.manifest_receipt},
        )

    def heartbeat(self, worker_id: str) -> CoordinatorEvent:
        heartbeat = self.registry.heartbeat(worker_id)
        return self.ledger.append(
            "worker_heartbeat",
            worker_id=worker_id,
            payload={
                "sequence": heartbeat.sequence,
                "manifest_receipt": heartbeat.manifest_receipt,
                "heartbeat_receipt": heartbeat.heartbeat_receipt,
            },
        )

    def assign(
        self,
        shard_id: int,
        worker_id: str,
        *,
        lease_ttl_seconds: float = 30.0,
        heartbeat_ttl_seconds: float = 30.0,
    ) -> CoordinatorEvent:
        state = self._state(shard_id)
        if state.status not in {"pending", "retry_pending"}:
            raise ValueError(f"shard {shard_id} cannot be assigned from state {state.status}")
        next_attempt = state.attempt + 1
        if next_attempt > self.max_attempts:
            state.status = "exhausted"
            raise ValueError("shard retry budget exhausted")
        lease = self.leases.acquire(
            shard_id,
            worker_id,
            lease_ttl_seconds=lease_ttl_seconds,
            heartbeat_ttl_seconds=heartbeat_ttl_seconds,
        )
        state.status = "assigned"
        state.attempt = next_attempt
        state.worker_id = worker_id
        state.lease_token = lease.lease_token
        state.failure_receipt = None
        return self.ledger.append(
            "shard_assigned",
            shard_id=shard_id,
            worker_id=worker_id,
            attempt=state.attempt,
            payload={"lease_token": lease.lease_token, "lease_epoch": lease.epoch},
        )

    def acknowledge(self, shard_id: int, worker_id: str) -> CoordinatorEvent:
        state = self._owned_state(shard_id, worker_id, allowed={"assigned"})
        state.status = "acked"
        return self.ledger.append(
            "shard_acknowledged",
            shard_id=shard_id,
            worker_id=worker_id,
            attempt=state.attempt,
            payload={"lease_token": state.lease_token},
        )

    def succeed(self, shard_id: int, worker_id: str, checkpoint_receipt: str) -> CoordinatorEvent:
        if not checkpoint_receipt:
            raise ValueError("checkpoint_receipt cannot be empty")
        state = self._owned_state(shard_id, worker_id, allowed={"acked"})
        lease = self.leases.active.get(shard_id)
        if lease is None or lease.lease_token != state.lease_token:
            raise ValueError("active lease missing at success")
        self.leases.release(lease)
        state.status = "succeeded"
        state.checkpoint_receipt = checkpoint_receipt
        return self.ledger.append(
            "shard_succeeded",
            shard_id=shard_id,
            worker_id=worker_id,
            attempt=state.attempt,
            payload={"checkpoint_receipt": checkpoint_receipt, "lease_token": state.lease_token},
        )

    def fail(self, shard_id: int, worker_id: str, failure_receipt: str) -> tuple[CoordinatorEvent, ...]:
        if not failure_receipt:
            raise ValueError("failure_receipt cannot be empty")
        state = self._owned_state(shard_id, worker_id, allowed={"assigned", "acked"})
        lease = self.leases.active.get(shard_id)
        if lease is not None and lease.lease_token == state.lease_token:
            self.leases.release(lease)
        state.failure_receipt = failure_receipt
        failure = self.ledger.append(
            "shard_failed",
            shard_id=shard_id,
            worker_id=worker_id,
            attempt=state.attempt,
            payload={"failure_receipt": failure_receipt, "lease_token": state.lease_token},
        )
        return (failure,) + self._schedule_retry_or_exhaust(state, reason="failure")

    def expire_leases(self) -> tuple[CoordinatorEvent, ...]:
        events: list[CoordinatorEvent] = []
        for lease in self.leases.expire():
            state = self._state(lease.shard_id)
            if state.status not in {"assigned", "acked"} or state.lease_token != lease.lease_token:
                continue
            expiry = self.ledger.append(
                "lease_expired",
                shard_id=lease.shard_id,
                worker_id=lease.worker_id,
                attempt=state.attempt,
                payload={"lease_token": lease.lease_token, "lease_epoch": lease.epoch},
            )
            events.append(expiry)
            events.extend(self._schedule_retry_or_exhaust(state, reason="lease_expired"))
        return tuple(events)

    def summary(self) -> dict[str, Any]:
        states = tuple(self.shard_states[key].to_dict() for key in sorted(self.shard_states))
        return {
            "plan_receipt": self.manifest.plan_receipt,
            "head_receipt": self.ledger.head_receipt,
            "event_count": len(self.ledger.events),
            "terminal": all(state["status"] in TERMINAL_SHARD_STATES for state in states),
            "successful_shards": sum(1 for state in states if state["status"] == "succeeded"),
            "exhausted_shards": sum(1 for state in states if state["status"] == "exhausted"),
            "shard_states": list(states),
        }

    def audit(self) -> CoordinatorAudit:
        flags: list[str] = []
        try:
            self.ledger.validate_chain()
        except ValueError as exc:
            flags.append(f"ledger:{exc}")
        try:
            replayed = replay_coordinator_events(self.manifest, self.ledger.events, max_attempts=self.max_attempts)
            for shard_id, state in self.shard_states.items():
                other = replayed[shard_id]
                if state.to_dict() != other.to_dict():
                    flags.append(f"state_mismatch:{shard_id}")
        except ValueError as exc:
            flags.append(f"replay:{exc}")
        return CoordinatorAudit(
            accepted=not flags,
            flags=tuple(flags),
            head_receipt=self.ledger.head_receipt,
            shard_states=tuple(self.shard_states[key].to_dict() for key in sorted(self.shard_states)),
        )

    def _state(self, shard_id: int) -> ShardCoordinatorState:
        try:
            return self.shard_states[int(shard_id)]
        except KeyError as exc:
            raise ValueError(f"unknown shard ID: {shard_id}") from exc

    def _owned_state(self, shard_id: int, worker_id: str, *, allowed: set[str]) -> ShardCoordinatorState:
        state = self._state(shard_id)
        if state.status not in allowed:
            raise ValueError(f"shard {shard_id} state {state.status} not in {sorted(allowed)}")
        if state.worker_id != worker_id:
            raise ValueError("worker does not own shard")
        return state

    def _schedule_retry_or_exhaust(self, state: ShardCoordinatorState, *, reason: str) -> tuple[CoordinatorEvent, ...]:
        state.worker_id = None
        state.lease_token = None
        if state.attempt >= self.max_attempts:
            state.status = "exhausted"
            return ()
        state.status = "retry_pending"
        event = self.ledger.append(
            "retry_scheduled",
            shard_id=state.shard_id,
            attempt=state.attempt,
            payload={"next_attempt": state.attempt + 1, "reason": reason},
        )
        return (event,)


def replay_coordinator_events(
    manifest: CampaignManifest,
    events: Iterable[CoordinatorEvent],
    *,
    max_attempts: int,
) -> dict[int, ShardCoordinatorState]:
    manifest.validate()
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    ledger = CoordinatorLedger(manifest.plan_receipt, events=list(events))
    ledger.validate_chain()
    states = {shard.shard_id: ShardCoordinatorState(shard.shard_id) for shard in manifest.shards}
    registered_workers: set[str] = set()

    for event in ledger.events:
        if event.kind == "worker_registered":
            if not event.worker_id:
                raise ValueError("worker_registered missing worker_id")
            registered_workers.add(event.worker_id)
            continue
        if event.kind == "worker_heartbeat":
            if not event.worker_id or event.worker_id not in registered_workers:
                raise ValueError("heartbeat for unregistered worker")
            continue
        if event.shard_id is None or event.shard_id not in states:
            raise ValueError("shard event references unknown shard")
        state = states[event.shard_id]

        if event.kind == "shard_assigned":
            if not event.worker_id or event.worker_id not in registered_workers:
                raise ValueError("assignment to unregistered worker")
            if state.status not in {"pending", "retry_pending"}:
                raise ValueError("illegal assignment transition")
            if event.attempt != state.attempt + 1 or event.attempt > max_attempts:
                raise ValueError("assignment attempt mismatch")
            state.status = "assigned"
            state.attempt = int(event.attempt)
            state.worker_id = event.worker_id
            state.lease_token = str(event.payload.get("lease_token") or "")
            state.failure_receipt = None
            if not state.lease_token:
                raise ValueError("assignment missing lease token")
        elif event.kind == "shard_acknowledged":
            if state.status != "assigned" or state.worker_id != event.worker_id or state.attempt != event.attempt:
                raise ValueError("illegal acknowledgement transition")
            if event.payload.get("lease_token") != state.lease_token:
                raise ValueError("ack lease mismatch")
            state.status = "acked"
        elif event.kind == "shard_succeeded":
            if state.status != "acked" or state.worker_id != event.worker_id or state.attempt != event.attempt:
                raise ValueError("illegal success transition")
            if event.payload.get("lease_token") != state.lease_token:
                raise ValueError("success lease mismatch")
            checkpoint_receipt = str(event.payload.get("checkpoint_receipt") or "")
            if not checkpoint_receipt:
                raise ValueError("success missing checkpoint receipt")
            state.status = "succeeded"
            state.checkpoint_receipt = checkpoint_receipt
        elif event.kind in {"shard_failed", "lease_expired"}:
            if state.status not in {"assigned", "acked"} or state.attempt != event.attempt:
                raise ValueError("illegal failure/expiry transition")
            if event.payload.get("lease_token") != state.lease_token:
                raise ValueError("failure/expiry lease mismatch")
            if event.kind == "shard_failed":
                failure_receipt = str(event.payload.get("failure_receipt") or "")
                if not failure_receipt:
                    raise ValueError("failure missing receipt")
                state.failure_receipt = failure_receipt
            state.worker_id = None
            state.lease_token = None
            state.status = "exhausted" if state.attempt >= max_attempts else "retry_pending"
        elif event.kind == "retry_scheduled":
            if state.status != "retry_pending":
                raise ValueError("retry scheduled from non-retry state")
            if int(event.payload.get("next_attempt", -1)) != state.attempt + 1:
                raise ValueError("retry next attempt mismatch")
        else:
            raise ValueError(f"unexpected coordinator event kind: {event.kind}")
    return states
