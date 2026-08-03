from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .model import CellRecord, RuntimePolicy, canonical_json, stable_digest

SCHEMA_VERSION = 10


class AtlasStore:
    def __init__(self, db_path: str | Path, policy: RuntimePolicy) -> None:
        self.db_path = Path(db_path)
        self.policy = policy
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute(f"PRAGMA busy_timeout={policy.sqlite_busy_timeout_ms}")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "AtlasStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cells (
                sequence INTEGER PRIMARY KEY,
                cell_id TEXT NOT NULL UNIQUE,
                problem_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                front TEXT NOT NULL,
                method TEXT NOT NULL,
                priority INTEGER NOT NULL,
                source_ref TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                cell_digest TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cells_problem ON cells(problem_id);
            CREATE INDEX IF NOT EXISTS idx_cells_target ON cells(target_id);
            CREATE INDEX IF NOT EXISTS idx_cells_front_priority
                ON cells(front, priority DESC, cell_id);

            CREATE TABLE IF NOT EXISTS duplicates (
                duplicate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ordinal INTEGER NOT NULL,
                cell_id TEXT NOT NULL,
                existing_digest TEXT NOT NULL,
                incoming_digest TEXT NOT NULL,
                exact_duplicate INTEGER NOT NULL,
                receipt_digest TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quarantine (
                quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ordinal INTEGER NOT NULL,
                cell_id TEXT,
                reason TEXT NOT NULL,
                raw_digest TEXT NOT NULL,
                raw_excerpt TEXT NOT NULL,
                receipt_digest TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_name TEXT PRIMARY KEY,
                checkpoint_json TEXT NOT NULL,
                checkpoint_digest TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS shards (
                shard_id INTEGER PRIMARY KEY,
                first_sequence INTEGER NOT NULL,
                last_sequence INTEGER NOT NULL,
                row_count INTEGER NOT NULL,
                byte_count INTEGER NOT NULL,
                merkle_root TEXT NOT NULL,
                shard_digest TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rollback_receipts (
                rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ordinal INTEGER NOT NULL,
                reason TEXT NOT NULL,
                checkpoint_digest TEXT,
                receipt_digest TEXT NOT NULL
            );
            """
        )
        self.set_metadata("schema_version", SCHEMA_VERSION)
        self.set_metadata("permanent_total_cell_cap", None)
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

    def set_metadata(self, key: str, value: Any) -> None:
        self.connection.execute(
            "INSERT INTO metadata(key, value_json) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
            (key, canonical_json(value)),
        )

    def get_metadata(self, key: str, default: Any = None) -> Any:
        row = self.connection.execute(
            "SELECT value_json FROM metadata WHERE key=?", (key,)
        ).fetchone()
        return default if row is None else json.loads(row["value_json"])

    def load_checkpoint(self, name: str = "main") -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT checkpoint_json, checkpoint_digest FROM checkpoints WHERE checkpoint_name=?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        value = json.loads(row["checkpoint_json"])
        if stable_digest(value) != row["checkpoint_digest"]:
            raise ValueError("checkpoint_digest_mismatch")
        return value

    def save_checkpoint(self, value: Mapping[str, Any], name: str = "main") -> str:
        payload = dict(value)
        digest = stable_digest(payload)
        self.connection.execute(
            "INSERT INTO checkpoints(checkpoint_name, checkpoint_json, checkpoint_digest) "
            "VALUES(?, ?, ?) ON CONFLICT(checkpoint_name) DO UPDATE SET "
            "checkpoint_json=excluded.checkpoint_json, checkpoint_digest=excluded.checkpoint_digest",
            (name, canonical_json(payload), digest),
        )
        return digest

    def next_sequence(self) -> int:
        row = self.connection.execute("SELECT COALESCE(MAX(sequence), 0) AS value FROM cells").fetchone()
        return int(row["value"]) + 1

    def insert_cell(self, sequence: int, source_ordinal: int, cell: CellRecord) -> str:
        existing = self.connection.execute(
            "SELECT cell_digest FROM cells WHERE cell_id=?", (cell.cell_id,)
        ).fetchone()
        if existing is not None:
            exact = existing["cell_digest"] == cell.digest
            receipt = {
                "source_ordinal": source_ordinal,
                "cell_id": cell.cell_id,
                "existing_digest": existing["cell_digest"],
                "incoming_digest": cell.digest,
                "exact_duplicate": exact,
            }
            self.connection.execute(
                "INSERT INTO duplicates(source_ordinal, cell_id, existing_digest, incoming_digest, "
                "exact_duplicate, receipt_digest) VALUES(?, ?, ?, ?, ?, ?)",
                (
                    source_ordinal,
                    cell.cell_id,
                    existing["cell_digest"],
                    cell.digest,
                    1 if exact else 0,
                    stable_digest(receipt),
                ),
            )
            if not exact:
                self.quarantine(
                    source_ordinal,
                    "duplicate_id_digest_conflict",
                    canonical_json(cell.to_dict()),
                    cell_id=cell.cell_id,
                )
                return "quarantined"
            return "duplicate"

        self.connection.execute(
            "INSERT INTO cells(sequence, cell_id, problem_id, target_id, front, method, priority, "
            "source_ref, payload_json, cell_digest) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sequence,
                cell.cell_id,
                cell.problem_id,
                cell.target_id,
                cell.front,
                cell.method,
                cell.priority,
                cell.source_ref,
                canonical_json(cell.payload),
                cell.digest,
            ),
        )
        return "inserted"

    def quarantine(
        self,
        source_ordinal: int,
        reason: str,
        raw_text: str,
        *,
        cell_id: str | None = None,
    ) -> str:
        raw_digest = stable_digest(raw_text)
        excerpt = raw_text[:512]
        receipt = {
            "source_ordinal": source_ordinal,
            "cell_id": cell_id,
            "reason": reason,
            "raw_digest": raw_digest,
            "raw_excerpt": excerpt,
        }
        digest = stable_digest(receipt)
        self.connection.execute(
            "INSERT INTO quarantine(source_ordinal, cell_id, reason, raw_digest, raw_excerpt, "
            "receipt_digest) VALUES(?, ?, ?, ?, ?, ?)",
            (source_ordinal, cell_id, reason, raw_digest, excerpt, digest),
        )
        return digest

    def record_rollback(
        self,
        source_ordinal: int,
        reason: str,
        checkpoint_digest: str | None,
    ) -> str:
        receipt = {
            "source_ordinal": source_ordinal,
            "reason": reason,
            "checkpoint_digest": checkpoint_digest,
        }
        digest = stable_digest(receipt)
        self.connection.execute(
            "INSERT INTO rollback_receipts(source_ordinal, reason, checkpoint_digest, receipt_digest) "
            "VALUES(?, ?, ?, ?)",
            (source_ordinal, reason, checkpoint_digest, digest),
        )
        self.connection.commit()
        return digest

    def add_shard(self, shard: Mapping[str, Any]) -> None:
        payload = dict(shard)
        digest = stable_digest(payload)
        self.connection.execute(
            "INSERT OR REPLACE INTO shards(shard_id, first_sequence, last_sequence, row_count, "
            "byte_count, merkle_root, shard_digest) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (
                payload["shard_id"],
                payload["first_sequence"],
                payload["last_sequence"],
                payload["row_count"],
                payload["byte_count"],
                payload["merkle_root"],
                digest,
            ),
        )

    def counts(self) -> dict[str, int]:
        tables = ("cells", "duplicates", "quarantine", "shards", "rollback_receipts")
        return {
            table: int(self.connection.execute(f"SELECT COUNT(*) AS value FROM {table}").fetchone()["value"])
            for table in tables
        }

    def iter_cells(self, chunk_size: int = 10_000) -> Iterable[list[sqlite3.Row]]:
        cursor = self.connection.execute("SELECT * FROM cells ORDER BY sequence")
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows

    def iter_shards(self) -> Iterable[sqlite3.Row]:
        yield from self.connection.execute("SELECT * FROM shards ORDER BY shard_id")

    def query_portfolio(
        self,
        *,
        limit: int,
        max_per_front: int,
        min_priority: int | None = None,
    ) -> list[dict[str, Any]]:
        if limit < 1 or max_per_front < 1:
            raise ValueError("limit and max_per_front must be positive")
        params: list[Any] = []
        where = ""
        if min_priority is not None:
            where = "WHERE priority >= ?"
            params.append(min_priority)
        params.extend([max_per_front, limit])
        rows = self.connection.execute(
            f"""
            WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY front ORDER BY priority DESC, cell_id ASC
                ) AS front_rank
                FROM cells
                {where}
            )
            SELECT cell_id, problem_id, target_id, front, method, priority,
                   source_ref, cell_digest, front_rank
            FROM ranked
            WHERE front_rank <= ?
            ORDER BY front_rank ASC, priority DESC, front ASC, cell_id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def database_bytes(self) -> int:
        total = self.db_path.stat().st_size if self.db_path.exists() else 0
        wal = self.db_path.with_name(self.db_path.name + "-wal")
        shm = self.db_path.with_name(self.db_path.name + "-shm")
        if wal.exists():
            total += wal.stat().st_size
        if shm.exists():
            total += shm.stat().st_size
        return total

    def enforce_disk_budget(self) -> None:
        if self.policy.max_disk_bytes is None:
            return
        current = self.database_bytes()
        if current > self.policy.max_disk_bytes:
            raise OSError(f"disk_budget_exceeded:{current}>{self.policy.max_disk_bytes}")
