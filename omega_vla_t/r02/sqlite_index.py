"""Disk-backed exact deduplication for large Ω-VLA campaigns."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping

from .dedup import content_digest


@dataclass(frozen=True)
class SQLiteIndexStats:
    path: str
    unique_digests: int
    duplicate_attempts: int
    inserted_attempts: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "unique_digests": self.unique_digests,
            "duplicate_attempts": self.duplicate_attempts,
            "inserted_attempts": self.inserted_attempts,
        }


class SQLiteDigestIndex:
    """Persistent SHA-256 set with bounded Python memory usage.

    SQLite remains finite and resource-bound. The class removes a fixed Python
    set ceiling; it does not claim unlimited disk, I/O throughput or durability.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        commit_interval: int = 1024,
        reset: bool = False,
    ) -> None:
        if commit_interval <= 0:
            raise ValueError("commit_interval must be positive")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if reset:
            for candidate in (
                self.path,
                Path(f"{self.path}-wal"),
                Path(f"{self.path}-shm"),
            ):
                if candidate.exists():
                    candidate.unlink()
        self.commit_interval = int(commit_interval)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS digests (
                digest TEXT PRIMARY KEY,
                first_seen_ordinal INTEGER NOT NULL,
                artifact_id TEXT,
                payload_type TEXT
            ) WITHOUT ROWID
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            ) WITHOUT ROWID
            """
        )
        self._pending = 0
        self._inserted_attempts = 0
        self._duplicate_attempts = 0

    def __enter__(self) -> "SQLiteDigestIndex":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.connection.rollback()
        self.close()

    def set_metadata(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
            (key, value),
        )
        self._pending += 1
        self._commit_if_needed()

    def metadata(self) -> dict[str, str]:
        rows = self.connection.execute(
            "SELECT key, value FROM metadata ORDER BY key"
        ).fetchall()
        return {str(key): str(value) for key, value in rows}

    def add(
        self,
        payload: Mapping[str, Any],
        *,
        ordinal: int,
    ) -> tuple[bool, str]:
        digest = content_digest(payload)
        artifact_id = payload.get("cell_id") or payload.get("artifact_id")
        payload_type = payload.get("object_family") or payload.get("artifact_type")
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO digests(
                digest, first_seen_ordinal, artifact_id, payload_type
            ) VALUES (?, ?, ?, ?)
            """,
            (
                digest,
                int(ordinal),
                None if artifact_id is None else str(artifact_id),
                None if payload_type is None else str(payload_type),
            ),
        )
        inserted = cursor.rowcount == 1
        if inserted:
            self._inserted_attempts += 1
        else:
            self._duplicate_attempts += 1
        self._pending += 1
        self._commit_if_needed()
        return inserted, digest

    def contains_digest(self, digest: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM digests WHERE digest = ? LIMIT 1", (digest,)
        ).fetchone()
        return row is not None

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM digests").fetchone()
        return int(row[0])

    def iter_digests(self, *, batch_size: int = 4096) -> Iterable[str]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        cursor = self.connection.execute(
            "SELECT digest FROM digests ORDER BY digest"
        )
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for (digest,) in rows:
                yield str(digest)

    def stats(self) -> SQLiteIndexStats:
        return SQLiteIndexStats(
            path=str(self.path),
            unique_digests=self.count(),
            duplicate_attempts=self._duplicate_attempts,
            inserted_attempts=self._inserted_attempts,
        )

    def commit(self) -> None:
        self.connection.commit()
        self._pending = 0

    def close(self) -> None:
        self.connection.close()

    def _commit_if_needed(self) -> None:
        if self._pending >= self.commit_interval:
            self.commit()
