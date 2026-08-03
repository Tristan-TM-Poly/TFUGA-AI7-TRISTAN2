from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Iterator, Mapping

from .models import TERMINAL_STATES, WORK_STATES, WorkRecord, canonical_json, stable_digest


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"ready", "blocked", "cancelled"}),
    "ready": frozenset({"running", "blocked", "cancelled"}),
    "running": frozenset({"ready", "validated", "rejected", "blocked", "cancelled"}),
    "validated": frozenset(),
    "rejected": frozenset({"ready", "cancelled"}),
    "blocked": frozenset({"ready", "cancelled"}),
    "cancelled": frozenset(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IntentLedger:
    """SQLite/WAL state store for resumable intent execution.

    The ledger is append-audited and performs no remote mutation. It supports
    idempotent ingestion, validated state transitions, exact checkpoints,
    content-addressed artifacts, residual memory and cooperative leases.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS intents (
                intent_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                digest TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS work_records (
                record_id TEXT PRIMARY KEY,
                intent_id TEXT NOT NULL REFERENCES intents(intent_id),
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                dependency_json TEXT NOT NULL,
                risk TEXT NOT NULL,
                state TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                content_digest TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS work_content_identity
                ON work_records(intent_id, content_digest);
            CREATE INDEX IF NOT EXISTS work_state_index
                ON work_records(intent_id, state, kind);

            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                intent_id TEXT NOT NULL,
                record_id TEXT,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkpoints (
                intent_id TEXT NOT NULL,
                checkpoint_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                digest TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(intent_id, checkpoint_key)
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                intent_id TEXT NOT NULL,
                record_id TEXT,
                path TEXT NOT NULL,
                digest TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS artifact_identity
                ON artifacts(intent_id, digest, path);

            CREATE TABLE IF NOT EXISTS residuals (
                residual_id TEXT PRIMARY KEY,
                intent_id TEXT NOT NULL,
                record_id TEXT,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                resolved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS leases (
                record_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def __enter__(self) -> "IntentLedger":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def ingest_intent(self, payload: Mapping[str, Any], *, state: str = "compiled") -> str:
        intent_id = str(payload.get("id") or payload.get("intent_id") or "").strip()
        if not intent_id:
            intent_id = f"INTENT2-{stable_digest(dict(payload))[:20].upper()}"
        normalized = {"id": intent_id, **dict(payload)}
        digest = stable_digest(normalized)
        now = _utc_now()
        with self.transaction():
            row = self.connection.execute(
                "SELECT digest FROM intents WHERE intent_id = ?", (intent_id,)
            ).fetchone()
            if row is not None and row["digest"] != digest:
                raise ValueError(f"intent identity collision: {intent_id}")
            self.connection.execute(
                """
                INSERT INTO intents(intent_id, payload_json, digest, state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(intent_id) DO UPDATE SET
                    state = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (intent_id, canonical_json(normalized), digest, state, now, now),
            )
            self._event_locked(intent_id, None, "intent_ingested", {"digest": digest, "state": state})
        return intent_id

    def ingest_work(self, record: WorkRecord) -> tuple[WorkRecord, bool]:
        now = _utc_now()
        with self.transaction():
            if self.connection.execute(
                "SELECT 1 FROM intents WHERE intent_id = ?", (record.intent_id,)
            ).fetchone() is None:
                raise KeyError(f"unknown intent: {record.intent_id}")
            existing = self.connection.execute(
                "SELECT * FROM work_records WHERE intent_id = ? AND content_digest = ?",
                (record.intent_id, record.content_digest),
            ).fetchone()
            if existing is not None:
                return self._row_to_work(existing), False
            self.connection.execute(
                """
                INSERT INTO work_records(
                    record_id, intent_id, kind, payload_json, dependency_json, risk,
                    state, attempts, content_digest, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.intent_id,
                    record.kind,
                    canonical_json(dict(record.payload)),
                    canonical_json(list(record.dependency_ids)),
                    record.risk,
                    record.state,
                    record.attempts,
                    record.content_digest,
                    canonical_json(dict(record.metadata)),
                    now,
                    now,
                ),
            )
            self._event_locked(
                record.intent_id,
                record.record_id,
                "work_ingested",
                {"state": record.state, "digest": record.content_digest},
            )
        return record, True

    def ingest_many(self, records: Iterable[WorkRecord]) -> tuple[int, int]:
        inserted = 0
        duplicates = 0
        for record in records:
            _, created = self.ingest_work(record)
            inserted += int(created)
            duplicates += int(not created)
        return inserted, duplicates

    def get_work(self, record_id: str) -> WorkRecord:
        row = self.connection.execute(
            "SELECT * FROM work_records WHERE record_id = ?", (record_id,)
        ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return self._row_to_work(row)

    def transition(
        self,
        record_id: str,
        new_state: str,
        *,
        reason: str,
        evidence: Iterable[str] = (),
        increment_attempt: bool = False,
    ) -> WorkRecord:
        if new_state not in WORK_STATES:
            raise ValueError(f"unknown work state: {new_state}")
        with self.transaction():
            row = self.connection.execute(
                "SELECT * FROM work_records WHERE record_id = ?", (record_id,)
            ).fetchone()
            if row is None:
                raise KeyError(record_id)
            current = str(row["state"])
            if new_state == current:
                return self._row_to_work(row)
            if new_state not in _ALLOWED_TRANSITIONS[current]:
                raise ValueError(f"illegal work transition: {current} -> {new_state}")
            attempts = int(row["attempts"]) + int(increment_attempt)
            now = _utc_now()
            self.connection.execute(
                "UPDATE work_records SET state = ?, attempts = ?, updated_at = ? WHERE record_id = ?",
                (new_state, attempts, now, record_id),
            )
            payload = {
                "from": current,
                "to": new_state,
                "reason": reason,
                "evidence": list(evidence),
                "attempts": attempts,
            }
            self._event_locked(str(row["intent_id"]), record_id, "state_transition", payload)
            updated = dict(row)
            updated["state"] = new_state
            updated["attempts"] = attempts
            return self._row_to_work(updated)

    def ready_if_dependencies_resolved(self, intent_id: str) -> int:
        records = {record.record_id: record for record in self.iter_work(intent_id)}
        promoted = 0
        for record in records.values():
            if record.state != "planned":
                continue
            missing = [dep for dep in record.dependency_ids if dep not in records]
            if missing:
                self.record_residual(
                    intent_id,
                    "missing_dependency",
                    {"record_id": record.record_id, "dependencies": missing},
                    record_id=record.record_id,
                    severity="error",
                )
                continue
            if all(records[dep].state == "validated" for dep in record.dependency_ids):
                self.transition(record.record_id, "ready", reason="dependencies_resolved")
                promoted += 1
        return promoted

    def iter_work(
        self,
        intent_id: str,
        *,
        states: Iterable[str] | None = None,
        kinds: Iterable[str] | None = None,
    ) -> Iterator[WorkRecord]:
        clauses = ["intent_id = ?"]
        params: list[Any] = [intent_id]
        if states:
            values = tuple(states)
            clauses.append(f"state IN ({','.join('?' for _ in values)})")
            params.extend(values)
        if kinds:
            values = tuple(kinds)
            clauses.append(f"kind IN ({','.join('?' for _ in values)})")
            params.extend(values)
        query = "SELECT * FROM work_records WHERE " + " AND ".join(clauses) + " ORDER BY record_id"
        for row in self.connection.execute(query, params):
            yield self._row_to_work(row)

    def save_checkpoint(self, intent_id: str, key: str, payload: Mapping[str, Any]) -> str:
        normalized = dict(payload)
        digest = stable_digest(normalized)
        now = _utc_now()
        with self.transaction():
            self.connection.execute(
                """
                INSERT INTO checkpoints(intent_id, checkpoint_key, payload_json, digest, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(intent_id, checkpoint_key) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    digest = excluded.digest,
                    created_at = excluded.created_at
                """,
                (intent_id, key, canonical_json(normalized), digest, now),
            )
            self._event_locked(intent_id, None, "checkpoint_saved", {"key": key, "digest": digest})
        return digest

    def load_checkpoint(self, intent_id: str, key: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload_json FROM checkpoints WHERE intent_id = ? AND checkpoint_key = ?",
            (intent_id, key),
        ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def register_artifact(
        self,
        intent_id: str,
        path: str,
        content: bytes | str,
        *,
        record_id: str | None = None,
        status: str = "generated",
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        encoded = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        digest = stable_digest({"sha256": __import__("hashlib").sha256(encoded).hexdigest(), "path": path})
        artifact_id = f"ART2-{digest[:20].upper()}"
        with self.transaction():
            self.connection.execute(
                """
                INSERT OR IGNORE INTO artifacts(
                    artifact_id, intent_id, record_id, path, digest, size_bytes,
                    status, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    intent_id,
                    record_id,
                    path,
                    digest,
                    len(encoded),
                    status,
                    canonical_json(dict(metadata or {})),
                    _utc_now(),
                ),
            )
            self._event_locked(intent_id, record_id, "artifact_registered", {"artifact_id": artifact_id})
        return artifact_id

    def record_residual(
        self,
        intent_id: str,
        category: str,
        payload: Mapping[str, Any],
        *,
        record_id: str | None = None,
        severity: str = "warning",
    ) -> str:
        identity = {
            "intent_id": intent_id,
            "record_id": record_id,
            "category": category,
            "severity": severity,
            "payload": dict(payload),
        }
        residual_id = f"M2-{stable_digest(identity)[:20].upper()}"
        with self.transaction():
            self.connection.execute(
                """
                INSERT OR IGNORE INTO residuals(
                    residual_id, intent_id, record_id, category, severity,
                    payload_json, resolved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    residual_id,
                    intent_id,
                    record_id,
                    category,
                    severity,
                    canonical_json(dict(payload)),
                    _utc_now(),
                ),
            )
            self._event_locked(intent_id, record_id, "residual_recorded", {"residual_id": residual_id})
        return residual_id

    def resolve_residual(self, residual_id: str) -> None:
        with self.transaction():
            row = self.connection.execute(
                "SELECT intent_id, record_id FROM residuals WHERE residual_id = ?", (residual_id,)
            ).fetchone()
            if row is None:
                raise KeyError(residual_id)
            self.connection.execute(
                "UPDATE residuals SET resolved = 1, resolved_at = ? WHERE residual_id = ?",
                (_utc_now(), residual_id),
            )
            self._event_locked(str(row["intent_id"]), row["record_id"], "residual_resolved", {"residual_id": residual_id})

    def acquire_lease(self, record_id: str, owner: str, *, ttl_seconds: int = 300) -> bool:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        with self.transaction():
            self.connection.execute("DELETE FROM leases WHERE expires_at <= ?", (now.isoformat(),))
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO leases(record_id, owner, acquired_at, expires_at) VALUES (?, ?, ?, ?)",
                (record_id, owner, now.isoformat(), expires.isoformat()),
            )
            return cursor.rowcount == 1

    def release_lease(self, record_id: str, owner: str) -> bool:
        with self.transaction():
            cursor = self.connection.execute(
                "DELETE FROM leases WHERE record_id = ? AND owner = ?", (record_id, owner)
            )
            return cursor.rowcount == 1

    def terminalize_batch(
        self,
        entries: Iterable[tuple[WorkRecord, str, Mapping[str, Any]]],
    ) -> dict[str, int]:
        """Atomically ingest and terminalize a validated batch.

        This is the high-throughput path used when an executor has already
        produced a finite outcome for every entry. It preserves content
        identity, one audit event per executed record and exact transaction
        rollback while avoiding several SQLite commits per work unit.
        """
        batch = tuple(entries)
        if not batch:
            return {"inserted": 0, "duplicates": 0, "validated": 0, "rejected": 0, "blocked": 0}
        allowed = {"validated", "rejected", "blocked"}
        if any(outcome not in allowed for _, outcome, _ in batch):
            raise ValueError("batch outcomes must be validated, rejected, or blocked")
        intent_ids = {record.intent_id for record, _, _ in batch}
        if len(intent_ids) != 1:
            raise ValueError("one atomic batch must belong to exactly one intent")
        intent_id = next(iter(intent_ids))
        now = _utc_now()
        result = {"inserted": 0, "duplicates": 0, "validated": 0, "rejected": 0, "blocked": 0}

        with self.transaction():
            if self.connection.execute(
                "SELECT 1 FROM intents WHERE intent_id = ?", (intent_id,)
            ).fetchone() is None:
                raise KeyError(f"unknown intent: {intent_id}")

            existing_by_digest: dict[str, sqlite3.Row] = {}
            digests = [record.content_digest for record, _, _ in batch]
            for start in range(0, len(digests), 400):
                chunk = digests[start : start + 400]
                rows = self.connection.execute(
                    f"SELECT * FROM work_records WHERE intent_id = ? AND content_digest IN ({','.join('?' for _ in chunk)})",
                    [intent_id, *chunk],
                )
                for row in rows:
                    existing_by_digest[str(row["content_digest"])] = row

            insert_rows: list[tuple[Any, ...]] = []
            update_rows: list[tuple[Any, ...]] = []
            event_rows: list[tuple[Any, ...]] = []
            for record, outcome, evidence in batch:
                existing = existing_by_digest.get(record.content_digest)
                if existing is not None and str(existing["state"]) in TERMINAL_STATES:
                    result["duplicates"] += 1
                    continue

                created = existing is None
                if created:
                    insert_rows.append(
                        (
                            record.record_id,
                            record.intent_id,
                            record.kind,
                            canonical_json(dict(record.payload)),
                            canonical_json(list(record.dependency_ids)),
                            record.risk,
                            outcome,
                            max(1, record.attempts + 1),
                            record.content_digest,
                            canonical_json(dict(record.metadata)),
                            now,
                            now,
                        )
                    )
                    record_id = record.record_id
                    result["inserted"] += 1
                else:
                    record_id = str(existing["record_id"])
                    update_rows.append((outcome, int(existing["attempts"]) + 1, now, record_id))
                result[outcome] += 1
                payload = {
                    "outcome": outcome,
                    "created": created,
                    "evidence": dict(evidence),
                    "atomic_batch": True,
                }
                event_id = f"EV2-{stable_digest((intent_id, record_id, payload, now))[:24].upper()}"
                event_rows.append(
                    (event_id, intent_id, record_id, "batch_terminalized", canonical_json(payload), now)
                )

            if insert_rows:
                self.connection.executemany(
                    """
                    INSERT INTO work_records(
                        record_id, intent_id, kind, payload_json, dependency_json, risk,
                        state, attempts, content_digest, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    insert_rows,
                )
            if update_rows:
                self.connection.executemany(
                    "UPDATE work_records SET state = ?, attempts = ?, updated_at = ? WHERE record_id = ?",
                    update_rows,
                )
            if event_rows:
                self.connection.executemany(
                    """
                    INSERT INTO events(event_id, intent_id, record_id, event_type, payload_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    event_rows,
                )
        return result

    def summary(self, intent_id: str) -> dict[str, Any]:
        counts = {
            str(row["state"]): int(row["count"])
            for row in self.connection.execute(
                "SELECT state, COUNT(*) AS count FROM work_records WHERE intent_id = ? GROUP BY state",
                (intent_id,),
            )
        }
        residuals = self.connection.execute(
            "SELECT COUNT(*) AS count FROM residuals WHERE intent_id = ? AND resolved = 0",
            (intent_id,),
        ).fetchone()["count"]
        artifacts = self.connection.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(size_bytes), 0) AS bytes FROM artifacts WHERE intent_id = ?",
            (intent_id,),
        ).fetchone()
        events = self.connection.execute(
            "SELECT COUNT(*) AS count FROM events WHERE intent_id = ?", (intent_id,)
        ).fetchone()["count"]
        total = sum(counts.values())
        terminal = sum(counts.get(state, 0) for state in TERMINAL_STATES)
        return {
            "schema": "omega-intent-ledger-summary/v2",
            "intent_id": intent_id,
            "work_total": total,
            "states": {state: counts.get(state, 0) for state in WORK_STATES},
            "terminal_ratio": terminal / total if total else 1.0,
            "open_residuals": int(residuals),
            "artifacts": int(artifacts["count"]),
            "artifact_bytes": int(artifacts["bytes"]),
            "events": int(events),
            "remote_mutations": 0,
            "automatic_merge": False,
        }

    def export_events(self, intent_id: str, path: str | Path) -> int:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for row in self.connection.execute(
                "SELECT * FROM events WHERE intent_id = ? ORDER BY sequence", (intent_id,)
            ):
                payload = {
                    "sequence": int(row["sequence"]),
                    "event_id": row["event_id"],
                    "intent_id": row["intent_id"],
                    "record_id": row["record_id"],
                    "event_type": row["event_type"],
                    "payload": json.loads(row["payload_json"]),
                    "created_at": row["created_at"],
                }
                handle.write(canonical_json(payload) + "\n")
                count += 1
        return count

    def _event_locked(
        self,
        intent_id: str,
        record_id: str | None,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> str:
        created_at = _utc_now()
        identity = {
            "intent_id": intent_id,
            "record_id": record_id,
            "event_type": event_type,
            "payload": dict(payload),
            "created_at": created_at,
        }
        event_id = f"EV2-{stable_digest(identity)[:24].upper()}"
        self.connection.execute(
            """
            INSERT INTO events(event_id, intent_id, record_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, intent_id, record_id, event_type, canonical_json(dict(payload)), created_at),
        )
        return event_id

    @staticmethod
    def _row_to_work(row: Mapping[str, Any]) -> WorkRecord:
        return WorkRecord(
            record_id=str(row["record_id"]),
            intent_id=str(row["intent_id"]),
            kind=str(row["kind"]),
            payload=json.loads(str(row["payload_json"])),
            dependency_ids=tuple(json.loads(str(row["dependency_json"]))),
            risk=str(row["risk"]),
            state=str(row["state"]),
            attempts=int(row["attempts"]),
            metadata=json.loads(str(row["metadata_json"])),
        )
