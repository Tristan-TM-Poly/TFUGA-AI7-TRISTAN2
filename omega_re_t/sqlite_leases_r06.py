"""Durable SQLite lease queue for finite authorized software campaigns."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class DurableLease:
    item_id: str
    lease_id: str
    worker_id: str
    payload_digest: str
    leased_at: int
    expires_at: int
    attempt: int


@dataclass(frozen=True)
class DurableResult:
    item_id: str
    worker_id: str
    result_digest: str
    committed_at: int
    attempt: int


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


class SQLiteLeaseQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_items (
                    item_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','leased','committed','failed')),
                    attempt INTEGER NOT NULL DEFAULT 0,
                    lease_id TEXT,
                    worker_id TEXT,
                    leased_at INTEGER,
                    expires_at INTEGER,
                    result_digest TEXT,
                    committed_at INTEGER
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    event_digest TEXT NOT NULL
                );
                """
            )

    def enqueue(self, items: Iterable[tuple[str, Mapping[str, Any]]]) -> int:
        inserted = 0
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                for item_id, payload in items:
                    if not item_id.strip():
                        raise ValueError("item id cannot be blank")
                    payload_json = _canonical(payload)
                    digest = _digest(payload)
                    cursor = connection.execute(
                        "INSERT OR IGNORE INTO work_items(item_id,payload_json,payload_digest,status) VALUES(?,?,?,'pending')",
                        (item_id, payload_json, digest),
                    )
                    inserted += cursor.rowcount
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return inserted

    def acquire(self, *, worker_id: str, now: int, ttl: int) -> DurableLease | None:
        if not worker_id.strip() or ttl <= 0:
            raise ValueError("worker id must be nonblank and ttl positive")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "UPDATE work_items SET status='pending',lease_id=NULL,worker_id=NULL,leased_at=NULL,expires_at=NULL "
                    "WHERE status='leased' AND expires_at<=?",
                    (now,),
                )
                row = connection.execute(
                    "SELECT * FROM work_items WHERE status='pending' ORDER BY item_id LIMIT 1"
                ).fetchone()
                if row is None:
                    connection.execute("COMMIT")
                    return None
                attempt = int(row["attempt"]) + 1
                lease_id = _digest({"item_id": row["item_id"], "worker_id": worker_id, "attempt": attempt, "now": now})
                expires = now + ttl
                connection.execute(
                    "UPDATE work_items SET status='leased',attempt=?,lease_id=?,worker_id=?,leased_at=?,expires_at=? WHERE item_id=?",
                    (attempt, lease_id, worker_id, now, expires, row["item_id"]),
                )
                self._event(connection, row["item_id"], "leased", {"lease_id": lease_id, "worker_id": worker_id, "expires_at": expires})
                connection.execute("COMMIT")
                return DurableLease(row["item_id"], lease_id, worker_id, row["payload_digest"], now, expires, attempt)
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def heartbeat(self, *, lease_id: str, worker_id: str, now: int, ttl: int) -> DurableLease:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM work_items WHERE lease_id=? AND worker_id=? AND status='leased'",
                    (lease_id, worker_id),
                ).fetchone()
                if row is None:
                    raise ValueError("active lease not found")
                if row["expires_at"] <= now:
                    raise ValueError("lease expired")
                expires = now + ttl
                connection.execute("UPDATE work_items SET expires_at=? WHERE item_id=?", (expires, row["item_id"]))
                self._event(connection, row["item_id"], "heartbeat", {"lease_id": lease_id, "expires_at": expires})
                connection.execute("COMMIT")
                return DurableLease(row["item_id"], lease_id, worker_id, row["payload_digest"], row["leased_at"], expires, row["attempt"])
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def commit(self, *, lease_id: str, worker_id: str, result: Mapping[str, Any], now: int) -> DurableResult:
        result_digest = _digest(result)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM work_items WHERE lease_id=? AND worker_id=?",
                    (lease_id, worker_id),
                ).fetchone()
                if row is None:
                    raise ValueError("lease not found")
                if row["status"] == "committed":
                    if row["result_digest"] != result_digest:
                        raise ValueError("equivocating duplicate result")
                    connection.execute("COMMIT")
                    return DurableResult(row["item_id"], worker_id, result_digest, row["committed_at"], row["attempt"])
                if row["status"] != "leased" or row["expires_at"] <= now:
                    raise ValueError("lease not active")
                connection.execute(
                    "UPDATE work_items SET status='committed',result_digest=?,committed_at=? WHERE item_id=?",
                    (result_digest, now, row["item_id"]),
                )
                self._event(connection, row["item_id"], "committed", {"result_digest": result_digest, "worker_id": worker_id})
                connection.execute("COMMIT")
                return DurableResult(row["item_id"], worker_id, result_digest, now, row["attempt"])
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def fail(self, *, lease_id: str, worker_id: str, now: int, retryable: bool) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM work_items WHERE lease_id=? AND worker_id=? AND status='leased'",
                    (lease_id, worker_id),
                ).fetchone()
                if row is None or row["expires_at"] <= now:
                    raise ValueError("active lease not found")
                status = "pending" if retryable else "failed"
                connection.execute(
                    "UPDATE work_items SET status=?,lease_id=NULL,worker_id=NULL,leased_at=NULL,expires_at=NULL WHERE item_id=?",
                    (status, row["item_id"]),
                )
                self._event(connection, row["item_id"], "failed", {"retryable": retryable, "worker_id": worker_id})
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def summary(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute("SELECT status,COUNT(*) AS count FROM work_items GROUP BY status").fetchall()
        result = {"pending": 0, "leased": 0, "committed": 0, "failed": 0}
        for row in rows:
            result[row["status"]] = row["count"]
        return result

    def event_chain(self) -> tuple[str, ...]:
        previous = "sha256:" + "0" * 64
        chain: list[str] = []
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY sequence").fetchall()
        for row in rows:
            previous = _digest({"previous": previous, "event_digest": row["event_digest"], "sequence": row["sequence"]})
            chain.append(previous)
        return tuple(chain)

    @staticmethod
    def _event(connection: sqlite3.Connection, item_id: str, event: str, payload: Mapping[str, Any]) -> None:
        event_json = _canonical(payload)
        connection.execute(
            "INSERT INTO events(item_id,event,event_json,event_digest) VALUES(?,?,?,?)",
            (item_id, event, event_json, _digest({"item_id": item_id, "event": event, "payload": payload})),
        )
