"""Deterministic JSONL/SQLite evidence storage with checkpoints."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sqlite3
from typing import Any, Iterator, Mapping


def canonical_json(value: Any) -> str:
    return dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def content_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Checkpoint:
    campaign_id: str
    sequence: int
    state: Mapping[str, Any]
    previous_hash: str
    checkpoint_hash: str

    @classmethod
    def create(
        cls,
        campaign_id: str,
        sequence: int,
        state: Mapping[str, Any],
        previous_hash: str = "0" * 64,
    ) -> "Checkpoint":
        payload = {
            "campaign_id": campaign_id,
            "sequence": sequence,
            "state": dict(state),
            "previous_hash": previous_hash,
        }
        return cls(
            campaign_id,
            sequence,
            dict(state),
            previous_hash,
            content_hash(payload),
        )

    def verify(self) -> bool:
        expected = content_hash(
            {
                "campaign_id": self.campaign_id,
                "sequence": self.sequence,
                "state": dict(self.state),
                "previous_hash": self.previous_hash,
            }
        )
        return expected == self.checkpoint_hash


class JSONLStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: Mapping[str, Any]) -> str:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        digest = content_hash(record)
        envelope = {"digest": digest, "record": dict(record)}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(envelope) + "\n")
        return digest

    def read(self, *, verify: bool = True) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return iter(())

        def iterator() -> Iterator[dict[str, Any]]:
            with self.path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    envelope = loads(line)
                    record = envelope["record"]
                    if (
                        verify
                        and content_hash(record) != envelope["digest"]
                    ):
                        raise ValueError(
                            f"digest mismatch at line {line_number}"
                        )
                    yield record

        return iterator()


class SQLiteEvidenceStore:
    SCHEMA_VERSION = 2

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._initialise()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SQLiteEvidenceStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _initialise(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS campaigns(
              campaign_id TEXT PRIMARY KEY,
              authorization_digest TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              status TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              row_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations(
              observation_id TEXT PRIMARY KEY,
              campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
              sequence INTEGER NOT NULL,
              payload_json TEXT NOT NULL,
              payload_hash TEXT NOT NULL,
              UNIQUE(campaign_id, sequence)
            );
            CREATE TABLE IF NOT EXISTS hypotheses(
              hypothesis_id TEXT NOT NULL,
              campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
              revision INTEGER NOT NULL,
              payload_json TEXT NOT NULL,
              payload_hash TEXT NOT NULL,
              PRIMARY KEY(hypothesis_id, campaign_id, revision)
            );
            CREATE TABLE IF NOT EXISTS artifacts(
              artifact_id TEXT PRIMARY KEY,
              campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
              kind TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              payload_hash TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS checkpoints(
              campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
              sequence INTEGER NOT NULL,
              state_json TEXT NOT NULL,
              previous_hash TEXT NOT NULL,
              checkpoint_hash TEXT NOT NULL,
              PRIMARY KEY(campaign_id, sequence)
            );
            """
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)",
            (str(self.SCHEMA_VERSION),),
        )
        self.connection.commit()

    @contextmanager
    def transaction(self):
        try:
            self.connection.execute("BEGIN")
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def create_campaign(
        self,
        campaign_id: str,
        authorization_digest: str,
        *,
        status: str = "planned",
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        payload = {
            "campaign_id": campaign_id,
            "authorization_digest": authorization_digest,
            "status": status,
            "metadata": dict(metadata or {}),
        }
        digest = content_hash(payload)
        self.connection.execute(
            "INSERT INTO campaigns(campaign_id,authorization_digest,status,metadata_json,row_hash) VALUES(?,?,?,?,?)",
            (
                campaign_id,
                authorization_digest,
                status,
                canonical_json(payload["metadata"]),
                digest,
            ),
        )
        self.connection.commit()
        return digest

    def add_observation(
        self,
        observation_id: str,
        campaign_id: str,
        sequence: int,
        payload: Mapping[str, Any],
    ) -> str:
        digest = content_hash(payload)
        self.connection.execute(
            "INSERT INTO observations VALUES(?,?,?,?,?)",
            (
                observation_id,
                campaign_id,
                sequence,
                canonical_json(payload),
                digest,
            ),
        )
        self.connection.commit()
        return digest

    def add_hypothesis(
        self,
        hypothesis_id: str,
        campaign_id: str,
        revision: int,
        payload: Mapping[str, Any],
    ) -> str:
        digest = content_hash(payload)
        self.connection.execute(
            "INSERT INTO hypotheses VALUES(?,?,?,?,?)",
            (
                hypothesis_id,
                campaign_id,
                revision,
                canonical_json(payload),
                digest,
            ),
        )
        self.connection.commit()
        return digest

    def add_artifact(
        self,
        artifact_id: str,
        campaign_id: str,
        kind: str,
        payload: Mapping[str, Any],
    ) -> str:
        digest = content_hash(payload)
        self.connection.execute(
            "INSERT INTO artifacts(artifact_id,campaign_id,kind,payload_json,payload_hash) VALUES(?,?,?,?,?)",
            (
                artifact_id,
                campaign_id,
                kind,
                canonical_json(payload),
                digest,
            ),
        )
        self.connection.commit()
        return digest

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        if not checkpoint.verify():
            raise ValueError("invalid checkpoint hash")
        self.connection.execute(
            "INSERT INTO checkpoints VALUES(?,?,?,?,?)",
            (
                checkpoint.campaign_id,
                checkpoint.sequence,
                canonical_json(checkpoint.state),
                checkpoint.previous_hash,
                checkpoint.checkpoint_hash,
            ),
        )
        self.connection.commit()

    def latest_checkpoint(
        self,
        campaign_id: str,
    ) -> Checkpoint | None:
        row = self.connection.execute(
            "SELECT * FROM checkpoints WHERE campaign_id=? ORDER BY sequence DESC LIMIT 1",
            (campaign_id,),
        ).fetchone()
        if row is None:
            return None
        return Checkpoint(
            row["campaign_id"],
            row["sequence"],
            loads(row["state_json"]),
            row["previous_hash"],
            row["checkpoint_hash"],
        )

    def observations(
        self,
        campaign_id: str,
    ) -> tuple[dict[str, Any], ...]:
        rows = self.connection.execute(
            "SELECT payload_json,payload_hash FROM observations WHERE campaign_id=? ORDER BY sequence",
            (campaign_id,),
        ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            payload = loads(row["payload_json"])
            if content_hash(payload) != row["payload_hash"]:
                raise ValueError("stored observation hash mismatch")
            result.append(payload)
        return tuple(result)

    def verify_campaign(self, campaign_id: str) -> tuple[str, ...]:
        errors: list[str] = []
        campaign = self.connection.execute(
            "SELECT * FROM campaigns WHERE campaign_id=?",
            (campaign_id,),
        ).fetchone()
        if campaign is None:
            return ("campaign_missing",)
        payload = {
            "campaign_id": campaign["campaign_id"],
            "authorization_digest": campaign["authorization_digest"],
            "status": campaign["status"],
            "metadata": loads(campaign["metadata_json"]),
        }
        if content_hash(payload) != campaign["row_hash"]:
            errors.append("campaign_hash_mismatch")
        for table in ("observations", "hypotheses", "artifacts"):
            rows = self.connection.execute(
                f"SELECT payload_json,payload_hash FROM {table} WHERE campaign_id=?",
                (campaign_id,),
            )
            for row in rows:
                if (
                    content_hash(loads(row["payload_json"]))
                    != row["payload_hash"]
                ):
                    errors.append(f"{table}_hash_mismatch")
        previous = "0" * 64
        rows = self.connection.execute(
            "SELECT * FROM checkpoints WHERE campaign_id=? ORDER BY sequence",
            (campaign_id,),
        )
        for row in rows:
            checkpoint = Checkpoint(
                row["campaign_id"],
                row["sequence"],
                loads(row["state_json"]),
                row["previous_hash"],
                row["checkpoint_hash"],
            )
            if row["previous_hash"] != previous:
                errors.append("checkpoint_chain_break")
            if not checkpoint.verify():
                errors.append("checkpoint_hash_mismatch")
            previous = row["checkpoint_hash"]
        return tuple(errors)
