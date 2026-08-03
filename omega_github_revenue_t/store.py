from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .ledger import reject_sensitive_fields
from .privacy import reject_secret_values
from .transparency import digest_payload


_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    assessment_json TEXT NOT NULL,
    score REAL NOT NULL,
    public_ready INTEGER NOT NULL,
    offer_ready INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS campaign_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_campaign_events_campaign
    ON campaign_events(campaign_id, sequence);
CREATE TABLE IF NOT EXISTS checkpoints (
    campaign_id TEXT PRIMARY KEY,
    source_offset INTEGER NOT NULL,
    accepted INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    quarantined INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    state_hash TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS provider_events (
    source TEXT NOT NULL,
    event_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    PRIMARY KEY(source, event_id)
);
"""


class CampaignStore:
    """Durable SQLite state for finite campaigns without a permanent item ceiling."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(_SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _safe_json(payload: Mapping[str, Any]) -> tuple[str, str]:
        reject_sensitive_fields(payload)
        reject_secret_values(payload)
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return encoded, digest_payload(payload)

    def upsert_artifact(
        self,
        artifact: Mapping[str, Any],
        assessment: Mapping[str, Any],
    ) -> str:
        artifact_json, artifact_hash = self._safe_json(artifact)
        assessment_json, _ = self._safe_json(assessment)
        artifact_id = str(artifact["artifact_id"])
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT payload_hash FROM artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
            if existing is not None and existing["payload_hash"] == artifact_hash:
                return "duplicate"
            connection.execute(
                """
                INSERT INTO artifacts(
                    artifact_id, payload_json, payload_hash, assessment_json,
                    score, public_ready, offer_ready
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    payload_hash = excluded.payload_hash,
                    assessment_json = excluded.assessment_json,
                    score = excluded.score,
                    public_ready = excluded.public_ready,
                    offer_ready = excluded.offer_ready,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    artifact_id,
                    artifact_json,
                    artifact_hash,
                    assessment_json,
                    float(assessment["score"]),
                    int(bool(assessment["public_ready"])),
                    int(bool(assessment["offer_ready"])),
                ),
            )
        return "updated" if existing is not None else "inserted"

    def upsert_artifacts_batch(
        self,
        pairs: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    ) -> dict[str, int]:
        counts = {"inserted": 0, "updated": 0, "duplicates": 0}
        with self.connect() as connection:
            for artifact, assessment in pairs:
                artifact_json, artifact_hash = self._safe_json(artifact)
                assessment_json, _ = self._safe_json(assessment)
                artifact_id = str(artifact["artifact_id"])
                existing = connection.execute(
                    "SELECT payload_hash FROM artifacts WHERE artifact_id = ?",
                    (artifact_id,),
                ).fetchone()
                if existing is not None and existing["payload_hash"] == artifact_hash:
                    counts["duplicates"] += 1
                    continue
                connection.execute(
                    """
                    INSERT INTO artifacts(
                        artifact_id, payload_json, payload_hash, assessment_json,
                        score, public_ready, offer_ready
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artifact_id) DO UPDATE SET
                        payload_json = excluded.payload_json,
                        payload_hash = excluded.payload_hash,
                        assessment_json = excluded.assessment_json,
                        score = excluded.score,
                        public_ready = excluded.public_ready,
                        offer_ready = excluded.offer_ready,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        artifact_id,
                        artifact_json,
                        artifact_hash,
                        assessment_json,
                        float(assessment["score"]),
                        int(bool(assessment["public_ready"])),
                        int(bool(assessment["offer_ready"])),
                    ),
                )
                counts["updated" if existing is not None else "inserted"] += 1
        return counts

    def iter_artifact_hashes(self, *, batch_size: int = 5000) -> Iterator[str]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last_id = ""
        while True:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT artifact_id, payload_hash
                    FROM artifacts
                    WHERE artifact_id > ?
                    ORDER BY artifact_id
                    LIMIT ?
                    """,
                    (last_id, batch_size),
                ).fetchall()
            if not rows:
                return
            for row in rows:
                last_id = str(row["artifact_id"])
                yield str(row["payload_hash"])

    def append_event(
        self,
        campaign_id: str,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> int:
        encoded, payload_hash = self._safe_json(payload)
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO campaign_events(
                    campaign_id, event_type, payload_json, payload_hash
                ) VALUES (?, ?, ?, ?)
                """,
                (campaign_id, event_type, encoded, payload_hash),
            )
            return int(cursor.lastrowid)

    def save_checkpoint(
        self,
        campaign_id: str,
        *,
        source_offset: int,
        accepted: int,
        duplicates: int,
        quarantined: int,
        state: Mapping[str, Any],
    ) -> str:
        if min(source_offset, accepted, duplicates, quarantined) < 0:
            raise ValueError("checkpoint counters must be non-negative")
        encoded, state_hash = self._safe_json(state)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO checkpoints(
                    campaign_id, source_offset, accepted, duplicates, quarantined,
                    state_json, state_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(campaign_id) DO UPDATE SET
                    source_offset = excluded.source_offset,
                    accepted = excluded.accepted,
                    duplicates = excluded.duplicates,
                    quarantined = excluded.quarantined,
                    state_json = excluded.state_json,
                    state_hash = excluded.state_hash,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    campaign_id,
                    source_offset,
                    accepted,
                    duplicates,
                    quarantined,
                    encoded,
                    state_hash,
                ),
            )
        return state_hash

    def load_checkpoint(self, campaign_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM checkpoints WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "campaign_id": row["campaign_id"],
            "source_offset": row["source_offset"],
            "accepted": row["accepted"],
            "duplicates": row["duplicates"],
            "quarantined": row["quarantined"],
            "state": json.loads(row["state_json"]),
            "state_hash": row["state_hash"],
        }

    def iter_artifacts(
        self,
        *,
        minimum_score: float = 0.0,
        batch_size: int = 1000,
    ) -> Iterator[dict[str, Any]]:
        if not 0 <= minimum_score <= 1:
            raise ValueError("minimum_score must be between 0 and 1")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        offset = 0
        while True:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT artifact_id, payload_json, assessment_json
                    FROM artifacts
                    WHERE score >= ?
                    ORDER BY score DESC, artifact_id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (minimum_score, batch_size, offset),
                ).fetchall()
            if not rows:
                return
            for row in rows:
                yield {
                    "artifact_id": row["artifact_id"],
                    "artifact": json.loads(row["payload_json"]),
                    "assessment": json.loads(row["assessment_json"]),
                }
            offset += len(rows)

    def count_artifacts(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS n FROM artifacts").fetchone()
        return int(row["n"])

    def ingest_provider_events(
        self,
        events: Iterable[Mapping[str, Any]],
    ) -> dict[str, int]:
        inserted = duplicates = 0
        with self.connect() as connection:
            for event in events:
                encoded, payload_hash = self._safe_json(event)
                source = str(event["source"])
                event_id = str(event["event_id"])
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO provider_events(
                        source, event_id, payload_json, payload_hash
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (source, event_id, encoded, payload_hash),
                )
                if cursor.rowcount:
                    inserted += 1
                else:
                    duplicates += 1
        return {"inserted": inserted, "duplicates": duplicates}
