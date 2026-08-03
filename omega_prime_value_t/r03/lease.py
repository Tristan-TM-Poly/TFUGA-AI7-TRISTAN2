from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


@dataclass(frozen=True, slots=True)
class LeaseTask:
    task_id: str
    payload: dict[str, Any]
    state: str
    lease_owner: str | None
    lease_until: int | None
    attempts: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LeaseStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('pending','leased','completed','failed')),
                    lease_owner TEXT,
                    lease_until INTEGER,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    detail_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_state_lease ON tasks(state, lease_until, task_id);
                """
            )

    def add_tasks(self, tasks: Iterable[tuple[str, dict[str, Any]]], *, now: int | None = None) -> int:
        timestamp = int(time.time()) if now is None else int(now)
        inserted = 0
        with self._transaction() as connection:
            for task_id, payload in tasks:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO tasks(task_id,payload_json,state,updated_at) VALUES(?,?, 'pending', ?)",
                    (task_id, json.dumps(payload, sort_keys=True, separators=(",", ":")), timestamp),
                )
                if cursor.rowcount:
                    inserted += 1
                    self._event(connection, task_id, "created", "system", timestamp, {})
        return inserted

    def claim(self, owner: str, *, limit: int = 1, lease_seconds: int = 60, now: int | None = None) -> list[LeaseTask]:
        if not owner or limit < 1 or lease_seconds < 1:
            raise ValueError("owner, positive limit and positive lease_seconds are required")
        timestamp = int(time.time()) if now is None else int(now)
        lease_until = timestamp + lease_seconds
        claimed: list[LeaseTask] = []
        with self._transaction() as connection:
            self._requeue_expired(connection, timestamp)
            rows = connection.execute(
                "SELECT task_id FROM tasks WHERE state='pending' ORDER BY task_id LIMIT ?",
                (limit,),
            ).fetchall()
            for row in rows:
                task_id = str(row["task_id"])
                connection.execute(
                    "UPDATE tasks SET state='leased', lease_owner=?, lease_until=?, attempts=attempts+1, updated_at=? WHERE task_id=? AND state='pending'",
                    (owner, lease_until, timestamp, task_id),
                )
                self._event(connection, task_id, "claimed", owner, timestamp, {"lease_until": lease_until})
            if rows:
                placeholders = ",".join("?" for _ in rows)
                claimed_rows = connection.execute(
                    f"SELECT * FROM tasks WHERE task_id IN ({placeholders}) ORDER BY task_id",
                    tuple(str(row["task_id"]) for row in rows),
                ).fetchall()
                claimed = [self._task(row) for row in claimed_rows]
        return claimed

    def renew(self, task_id: str, owner: str, *, lease_seconds: int = 60, now: int | None = None) -> bool:
        timestamp = int(time.time()) if now is None else int(now)
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET lease_until=?, updated_at=? WHERE task_id=? AND state='leased' AND lease_owner=? AND lease_until>=?",
                (timestamp + lease_seconds, timestamp, task_id, owner, timestamp),
            )
            if cursor.rowcount:
                self._event(connection, task_id, "renewed", owner, timestamp, {"lease_until": timestamp + lease_seconds})
            return bool(cursor.rowcount)

    def complete(self, task_id: str, owner: str, result: dict[str, Any], *, now: int | None = None) -> bool:
        return self._finish(task_id, owner, "completed", result, now)

    def fail(self, task_id: str, owner: str, result: dict[str, Any], *, now: int | None = None) -> bool:
        return self._finish(task_id, owner, "failed", result, now)

    def _finish(self, task_id: str, owner: str, state: str, result: dict[str, Any], now: int | None) -> bool:
        timestamp = int(time.time()) if now is None else int(now)
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET state=?, result_json=?, lease_owner=NULL, lease_until=NULL, updated_at=? WHERE task_id=? AND state='leased' AND lease_owner=? AND lease_until>=?",
                (state, json.dumps(result, sort_keys=True, separators=(",", ":")), timestamp, task_id, owner, timestamp),
            )
            if cursor.rowcount:
                self._event(connection, task_id, state, owner, timestamp, result)
            return bool(cursor.rowcount)

    def requeue_expired(self, *, now: int | None = None) -> int:
        timestamp = int(time.time()) if now is None else int(now)
        with self._transaction() as connection:
            return self._requeue_expired(connection, timestamp)

    def _requeue_expired(self, connection: sqlite3.Connection, timestamp: int) -> int:
        rows = connection.execute(
            "SELECT task_id, lease_owner FROM tasks WHERE state='leased' AND lease_until < ? ORDER BY task_id",
            (timestamp,),
        ).fetchall()
        for row in rows:
            task_id = str(row["task_id"])
            previous_owner = str(row["lease_owner"])
            connection.execute(
                "UPDATE tasks SET state='pending', lease_owner=NULL, lease_until=NULL, updated_at=? WHERE task_id=?",
                (timestamp, task_id),
            )
            self._event(connection, task_id, "lease_expired", "system", timestamp, {"previous_owner": previous_owner})
        return len(rows)

    def task(self, task_id: str) -> LeaseTask | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            return None if row is None else self._task(row)

    def stats(self) -> dict[str, int | bool]:
        with self._connect() as connection:
            counts = {row["state"]: int(row["count"]) for row in connection.execute("SELECT state, COUNT(*) AS count FROM tasks GROUP BY state")}
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            events = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        return {
            "pending": counts.get("pending", 0),
            "leased": counts.get("leased", 0),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
            "events": events,
            "integrity_check": integrity,
        }

    def events(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY sequence").fetchall()
        return [dict(row) | {"detail": json.loads(row["detail_json"])} for row in rows]

    @staticmethod
    def _task(row: sqlite3.Row) -> LeaseTask:
        return LeaseTask(
            task_id=str(row["task_id"]),
            payload=json.loads(row["payload_json"]),
            state=str(row["state"]),
            lease_owner=row["lease_owner"],
            lease_until=row["lease_until"],
            attempts=int(row["attempts"]),
        )

    @staticmethod
    def _event(connection: sqlite3.Connection, task_id: str, event_type: str, actor: str, timestamp: int, detail: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO events(task_id,event_type,actor,timestamp,detail_json) VALUES(?,?,?,?,?)",
            (task_id, event_type, actor, timestamp, json.dumps(detail, sort_keys=True, separators=(",", ":"))),
        )
