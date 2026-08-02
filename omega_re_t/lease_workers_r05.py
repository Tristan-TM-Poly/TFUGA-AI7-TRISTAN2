"""Deterministic lease queue for bounded distributed software campaigns.

The queue provides at-least-once execution semantics and exactly-once accepted
result commits per item identifier.  It does not launch external workers or
claim distributed-system certification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class WorkItem:
    item_id: str
    payload: Mapping[str, Any]

    @property
    def payload_digest(self) -> str:
        return _digest(self.payload)


@dataclass(frozen=True)
class Lease:
    item_id: str
    worker_id: str
    lease_id: str
    acquired_at: int
    expires_at: int
    attempt: int
    payload_digest: str


@dataclass(frozen=True)
class WorkResult:
    item_id: str
    worker_id: str
    lease_id: str
    result_digest: str
    accepted_at: int
    attempt: int


class LeaseQueue:
    def __init__(self, items: Iterable[WorkItem]) -> None:
        materialized = tuple(items)
        if not materialized:
            raise ValueError("items cannot be empty")
        self._items = {item.item_id: item for item in materialized}
        if len(self._items) != len(materialized):
            raise ValueError("item identifiers must be unique")
        self._leases: dict[str, Lease] = {}
        self._results: dict[str, WorkResult] = {}
        self._attempts: dict[str, int] = {item_id: 0 for item_id in self._items}

    @classmethod
    def from_items(cls, items: Iterable[WorkItem]) -> "LeaseQueue":
        return cls(items)

    @property
    def results(self) -> tuple[WorkResult, ...]:
        return tuple(self._results[key] for key in sorted(self._results))

    def _expire(self, now: int) -> None:
        for item_id, lease in list(self._leases.items()):
            if lease.expires_at <= now:
                del self._leases[item_id]

    def acquire(self, *, worker_id: str, now: int, ttl: int) -> Lease | None:
        if not worker_id.strip() or ttl <= 0:
            raise ValueError("worker_id must be nonblank and ttl positive")
        self._expire(now)
        for item_id in sorted(self._items):
            if item_id in self._results or item_id in self._leases:
                continue
            self._attempts[item_id] += 1
            attempt = self._attempts[item_id]
            lease_id = _digest(
                {
                    "item_id": item_id,
                    "worker_id": worker_id,
                    "attempt": attempt,
                    "acquired_at": now,
                }
            )
            lease = Lease(
                item_id=item_id,
                worker_id=worker_id,
                lease_id=lease_id,
                acquired_at=now,
                expires_at=now + ttl,
                attempt=attempt,
                payload_digest=self._items[item_id].payload_digest,
            )
            self._leases[item_id] = lease
            return lease
        return None

    def heartbeat(self, *, lease_id: str, worker_id: str, now: int, ttl: int) -> Lease:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._expire(now)
        lease = next((item for item in self._leases.values() if item.lease_id == lease_id), None)
        if lease is None:
            raise KeyError("lease not active")
        if lease.worker_id != worker_id:
            raise PermissionError("worker mismatch")
        updated = Lease(
            item_id=lease.item_id,
            worker_id=worker_id,
            lease_id=lease.lease_id,
            acquired_at=lease.acquired_at,
            expires_at=now + ttl,
            attempt=lease.attempt,
            payload_digest=lease.payload_digest,
        )
        self._leases[lease.item_id] = updated
        return updated

    def commit(self, *, lease_id: str, worker_id: str, result: Mapping[str, Any], now: int) -> WorkResult:
        self._expire(now)
        lease = next((item for item in self._leases.values() if item.lease_id == lease_id), None)
        if lease is None:
            raise KeyError("lease not active")
        if lease.worker_id != worker_id:
            raise PermissionError("worker mismatch")
        if lease.item_id in self._results:
            raise RuntimeError("result already committed")
        accepted = WorkResult(
            item_id=lease.item_id,
            worker_id=worker_id,
            lease_id=lease_id,
            result_digest=_digest(result),
            accepted_at=now,
            attempt=lease.attempt,
        )
        self._results[lease.item_id] = accepted
        del self._leases[lease.item_id]
        return accepted

    def summary(self, *, now: int) -> dict[str, Any]:
        self._expire(now)
        return {
            "logical_items": len(self._items),
            "completed_items": len(self._results),
            "active_leases": len(self._leases),
            "pending_items": len(self._items) - len(self._results) - len(self._leases),
            "attempts": dict(sorted(self._attempts.items())),
            "semantics": "at_least_once_execution_exactly_once_accepted_commit",
            "external_workers_launched": False,
        }
