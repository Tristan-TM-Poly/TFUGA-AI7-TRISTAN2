"""Transactional SQLite state for Ω-GENERATOR-DISCOVERY R0.5 workers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Any

from .frontier_virtual import FrontierReceipt, VirtualFrontierPlan, canonical_json


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    current = value or _utc_now()
    if current.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return current.astimezone(timezone.utc).isoformat()


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS plans (
    plan_fingerprint TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    requested_logical_records INTEGER NOT NULL,
    planned_logical_records INTEGER NOT NULL,
    epoch_count INTEGER NOT NULL,
    total_partition_count INTEGER NOT NULL,
    definition_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS partitions (
    plan_fingerprint TEXT NOT NULL,
    global_partition_index INTEGER NOT NULL,
    partition_key TEXT NOT NULL,
    epoch_index INTEGER NOT NULL,
    generator_start INTEGER NOT NULL,
    generator_stop INTEGER NOT NULL,
    logical_records INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    worker_id TEXT,
    lease_token TEXT,
    lease_expires_at TEXT,
    receipt_hash TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (plan_fingerprint, global_partition_index),
    UNIQUE (partition_key),
    FOREIGN KEY (plan_fingerprint) REFERENCES plans(plan_fingerprint)
);
CREATE INDEX IF NOT EXISTS idx_partitions_claim
ON partitions(plan_fingerprint, status, global_partition_index);
CREATE TABLE IF NOT EXISTS receipts (
    receipt_hash TEXT PRIMARY KEY,
    plan_fingerprint TEXT NOT NULL,
    partition_key TEXT NOT NULL UNIQUE,
    worker_id TEXT NOT NULL,
    logical_records INTEGER NOT NULL,
    generator_bundles INTEGER NOT NULL,
    mmr_root TEXT NOT NULL,
    leaf_count INTEGER NOT NULL,
    validation_status TEXT NOT NULL,
    previous_receipt_hash TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    receipt_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exact_dedup (
    content_fingerprint TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    kind TEXT NOT NULL,
    first_partition_key TEXT NOT NULL,
    payload_bytes INTEGER NOT NULL,
    first_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS frontier_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_fingerprint TEXT NOT NULL,
    event_type TEXT NOT NULL,
    partition_key TEXT,
    worker_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
PRAGMA user_version = 5;
"""


class FrontierStore:
    """Small durable control plane; payload shards remain outside the database."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def register_plan(self, plan: VirtualFrontierPlan) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO plans (
                    plan_fingerprint, campaign_id, requested_logical_records,
                    planned_logical_records, epoch_count, total_partition_count,
                    definition_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(plan_fingerprint) DO UPDATE SET
                    definition_json=excluded.definition_json
                """,
                (
                    plan.plan_fingerprint,
                    plan.shape.campaign_id,
                    plan.requested_logical_records,
                    plan.planned_logical_records,
                    plan.epoch_count,
                    plan.total_partition_count,
                    canonical_json(plan.to_dict()),
                    _iso(),
                ),
            )

    def seed_partition_page(
        self,
        plan: VirtualFrontierPlan,
        *,
        cursor: int = 0,
        limit: int = 256,
    ) -> int:
        self.register_plan(plan)
        rows = [
            (
                plan.plan_fingerprint,
                part.global_partition_index,
                part.partition_key,
                part.epoch_index,
                part.generator_start,
                part.generator_stop,
                part.logical_records,
                "pending",
                _iso(),
            )
            for part in plan.iter_partition_page(cursor, limit)
        ]
        if not rows:
            return 0
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO partitions (
                    plan_fingerprint, global_partition_index, partition_key,
                    epoch_index, generator_start, generator_stop,
                    logical_records, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(plan_fingerprint, global_partition_index) DO NOTHING
                """,
                rows,
            )
        return len(rows)

    def _expire_leases(
        self, connection: sqlite3.Connection, plan_fingerprint: str, now: str
    ) -> int:
        cursor = connection.execute(
            """
            UPDATE partitions
            SET status='pending', worker_id=NULL, lease_token=NULL,
                lease_expires_at=NULL, updated_at=?
            WHERE plan_fingerprint=? AND status='leased'
              AND lease_expires_at <= ?
            """,
            (now, plan_fingerprint, now),
        )
        return cursor.rowcount

    def claim(
        self,
        plan_fingerprint: str,
        worker_id: str,
        *,
        ttl_seconds: int = 3_600,
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        issued = now or _utc_now()
        if issued.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        issued = issued.astimezone(timezone.utc)
        expires = issued + timedelta(seconds=ttl_seconds)
        token = secrets.token_urlsafe(32)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._expire_leases(connection, plan_fingerprint, issued.isoformat())
            row = connection.execute(
                """
                SELECT * FROM partitions
                WHERE plan_fingerprint=? AND status='pending'
                ORDER BY global_partition_index
                LIMIT 1
                """,
                (plan_fingerprint,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            updated = connection.execute(
                """
                UPDATE partitions
                SET status='leased', worker_id=?, lease_token=?,
                    lease_expires_at=?, updated_at=?
                WHERE plan_fingerprint=? AND global_partition_index=?
                  AND status='pending'
                """,
                (
                    worker_id,
                    token,
                    expires.isoformat(),
                    issued.isoformat(),
                    plan_fingerprint,
                    int(row["global_partition_index"]),
                ),
            )
            if updated.rowcount != 1:
                connection.rollback()
                return None
            connection.execute(
                """
                INSERT INTO frontier_events (
                    plan_fingerprint, event_type, partition_key, worker_id,
                    payload_json, created_at
                ) VALUES (?, 'lease_claimed', ?, ?, ?, ?)
                """,
                (
                    plan_fingerprint,
                    row["partition_key"],
                    worker_id,
                    canonical_json(
                        {
                            "lease_token_sha256": hashlib.sha256(
                                token.encode("utf-8")
                            ).hexdigest(),
                            "expires_at": expires.isoformat(),
                        }
                    ),
                    issued.isoformat(),
                ),
            )
            connection.commit()
            return {
                "plan_fingerprint": plan_fingerprint,
                "global_partition_index": int(row["global_partition_index"]),
                "partition_key": str(row["partition_key"]),
                "epoch_index": int(row["epoch_index"]),
                "generator_start": int(row["generator_start"]),
                "generator_stop": int(row["generator_stop"]),
                "logical_records": int(row["logical_records"]),
                "worker_id": worker_id,
                "lease_token": token,
                "lease_expires_at": expires.isoformat(),
            }

    def heartbeat(
        self,
        lease_token: str,
        *,
        ttl_seconds: int = 3_600,
        now: datetime | None = None,
    ) -> bool:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        current = now or _utc_now()
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        expires = current.astimezone(timezone.utc) + timedelta(seconds=ttl_seconds)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE partitions
                SET lease_expires_at=?, updated_at=?
                WHERE lease_token=? AND status='leased'
                """,
                (expires.isoformat(), current.isoformat(), lease_token),
            )
            return cursor.rowcount == 1

    def complete(self, lease_token: str, receipt: FrontierReceipt) -> bool:
        if not receipt.verify():
            raise ValueError("receipt integrity verification failed")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM partitions WHERE lease_token=? AND status='leased'",
                (lease_token,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return False
            if (
                row["plan_fingerprint"] != receipt.plan_fingerprint
                or row["partition_key"] != receipt.partition_key
                or row["worker_id"] != receipt.worker_id
                or int(row["logical_records"]) != receipt.logical_records
            ):
                connection.rollback()
                raise ValueError("receipt does not match leased partition")
            connection.execute(
                """
                INSERT INTO receipts (
                    receipt_hash, plan_fingerprint, partition_key, worker_id,
                    logical_records, generator_bundles, mmr_root, leaf_count,
                    validation_status, previous_receipt_hash, completed_at,
                    receipt_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_hash,
                    receipt.plan_fingerprint,
                    receipt.partition_key,
                    receipt.worker_id,
                    receipt.logical_records,
                    receipt.generator_bundles,
                    receipt.mmr_root,
                    receipt.leaf_count,
                    receipt.validation_status,
                    receipt.previous_receipt_hash,
                    receipt.completed_at,
                    canonical_json(receipt.to_dict()),
                ),
            )
            connection.execute(
                """
                UPDATE partitions
                SET status='completed', receipt_hash=?, lease_token=NULL,
                    lease_expires_at=NULL, updated_at=?
                WHERE plan_fingerprint=? AND global_partition_index=?
                """,
                (
                    receipt.receipt_hash,
                    _iso(),
                    row["plan_fingerprint"],
                    int(row["global_partition_index"]),
                ),
            )
            connection.execute(
                """
                INSERT INTO frontier_events (
                    plan_fingerprint, event_type, partition_key, worker_id,
                    payload_json, created_at
                ) VALUES (?, 'partition_completed', ?, ?, ?, ?)
                """,
                (
                    receipt.plan_fingerprint,
                    receipt.partition_key,
                    receipt.worker_id,
                    canonical_json(
                        {
                            "receipt_hash": receipt.receipt_hash,
                            "validation_status": receipt.validation_status,
                            "mmr_root": receipt.mmr_root,
                        }
                    ),
                    receipt.completed_at,
                ),
            )
            connection.commit()
            return True

    def release(self, lease_token: str, *, reason: str = "worker_release") -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM partitions WHERE lease_token=? AND status='leased'",
                (lease_token,),
            ).fetchone()
            if row is None:
                return False
            connection.execute(
                """
                UPDATE partitions
                SET status='pending', worker_id=NULL, lease_token=NULL,
                    lease_expires_at=NULL, updated_at=?
                WHERE lease_token=? AND status='leased'
                """,
                (_iso(), lease_token),
            )
            connection.execute(
                """
                INSERT INTO frontier_events (
                    plan_fingerprint, event_type, partition_key, worker_id,
                    payload_json, created_at
                ) VALUES (?, 'lease_released', ?, ?, ?, ?)
                """,
                (
                    row["plan_fingerprint"],
                    row["partition_key"],
                    row["worker_id"],
                    canonical_json({"reason": reason}),
                    _iso(),
                ),
            )
            return True

    def register_exact_fingerprint(
        self,
        content_fingerprint: str,
        *,
        namespace: str,
        kind: str,
        first_partition_key: str,
        payload_bytes: int,
    ) -> bool:
        if payload_bytes < 0:
            raise ValueError("payload_bytes cannot be negative")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO exact_dedup (
                    content_fingerprint, namespace, kind, first_partition_key,
                    payload_bytes, first_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    content_fingerprint,
                    namespace,
                    kind,
                    first_partition_key,
                    payload_bytes,
                    _iso(),
                ),
            )
            return cursor.rowcount == 1

    def status(self, plan_fingerprint: str) -> dict[str, Any]:
        with self._connect() as connection:
            counts = {
                row["status"]: int(row["count"])
                for row in connection.execute(
                    """
                    SELECT status, COUNT(*) AS count
                    FROM partitions
                    WHERE plan_fingerprint=?
                    GROUP BY status
                    """,
                    (plan_fingerprint,),
                )
            }
            records = connection.execute(
                """
                SELECT COALESCE(SUM(logical_records), 0)
                FROM partitions
                WHERE plan_fingerprint=? AND status='completed'
                """,
                (plan_fingerprint,),
            ).fetchone()[0]
            receipt_count = connection.execute(
                "SELECT COUNT(*) FROM receipts WHERE plan_fingerprint=?",
                (plan_fingerprint,),
            ).fetchone()[0]
            return {
                "plan_fingerprint": plan_fingerprint,
                "partition_status": counts,
                "completed_logical_records": int(records),
                "receipt_count": int(receipt_count),
            }

    def integrity_audit(self, plan_fingerprint: str) -> dict[str, Any]:
        errors: list[str] = []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT p.partition_key, p.status, p.receipt_hash, r.receipt_json
                FROM partitions p
                LEFT JOIN receipts r ON r.receipt_hash = p.receipt_hash
                WHERE p.plan_fingerprint=?
                ORDER BY p.global_partition_index
                """,
                (plan_fingerprint,),
            ).fetchall()
            for row in rows:
                if row["status"] != "completed":
                    continue
                if not row["receipt_hash"] or not row["receipt_json"]:
                    errors.append(f"{row['partition_key']}: missing receipt")
                    continue
                receipt = FrontierReceipt(**json.loads(row["receipt_json"]))
                if not receipt.verify():
                    errors.append(f"{row['partition_key']}: invalid receipt hash")
        return {
            "status": "valid" if not errors else "invalid",
            "plan_fingerprint": plan_fingerprint,
            "partitions_audited": len(rows),
            "error_count": len(errors),
            "errors": errors[:100],
        }
