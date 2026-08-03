from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from .models import CampaignManifest, CandidateTask, TaskState

_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    manifest_sha256 TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_sequence INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    shard_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    family TEXT NOT NULL,
    exponent INTEGER NOT NULL,
    k TEXT NOT NULL,
    value TEXT NOT NULL,
    state TEXT NOT NULL,
    factor TEXT,
    certificate_id TEXT,
    certificate_sha256 TEXT,
    error TEXT,
    UNIQUE(campaign_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_tasks_campaign_state_ordinal
ON tasks(campaign_id, state, ordinal);
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    task_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS registry (
    fingerprint TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    certificate_id TEXT NOT NULL,
    certificate_sha256 TEXT NOT NULL,
    first_campaign_id TEXT NOT NULL
);
"""


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CampaignStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(_SCHEMA)
        self.connection.commit()

    def __enter__(self) -> "CampaignStore":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def load_manifest(self, manifest: CampaignManifest) -> int:
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO campaigns(campaign_id, manifest_sha256, manifest_json) VALUES(?,?,?)",
                (manifest.campaign_id, manifest.sha256, _json(manifest.to_dict())),
            )
            inserted = 0
            for task in manifest.tasks:
                cursor = self.connection.execute(
                    """
                    INSERT OR IGNORE INTO tasks(
                        task_id,campaign_id,shard_id,ordinal,family,exponent,k,value,state
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        task.task_id,
                        manifest.campaign_id,
                        task.shard_id,
                        task.ordinal,
                        task.family,
                        task.exponent,
                        str(task.k),
                        str(task.value),
                        task.state.value,
                    ),
                )
                inserted += cursor.rowcount
            self._event(manifest.campaign_id, None, "manifest_loaded", {"inserted": inserted})
        return inserted

    def _event(self, campaign_id: str, task_id: str | None, event_type: str, payload: Any) -> None:
        self.connection.execute(
            "INSERT INTO events(campaign_id,task_id,event_type,payload_json) VALUES(?,?,?,?)",
            (campaign_id, task_id, event_type, _json(payload)),
        )

    def iter_pending(self, campaign_id: str, *, limit: int | None = None) -> Iterator[CandidateTask]:
        sql = "SELECT * FROM tasks WHERE campaign_id=? AND state=? ORDER BY ordinal"
        params: list[Any] = [campaign_id, TaskState.PLANNED.value]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.connection.execute(sql, params)
        for row in rows:
            yield CandidateTask(
                task_id=row["task_id"],
                shard_id=row["shard_id"],
                ordinal=row["ordinal"],
                family=row["family"],
                exponent=row["exponent"],
                k=int(row["k"]),
                value=int(row["value"]),
                state=TaskState(row["state"]),
            )

    def update_task(
        self,
        task: CandidateTask,
        state: TaskState,
        *,
        factor: int | None = None,
        certificate: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        certificate_id = None if certificate is None else str(certificate["certificate_id"])
        certificate_sha = None if certificate is None else str(certificate["sha256"])
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE tasks SET state=?, factor=?, certificate_id=?, certificate_sha256=?, error=?
                WHERE task_id=? AND state=?
                """,
                (
                    state.value,
                    None if factor is None else str(factor),
                    certificate_id,
                    certificate_sha,
                    error,
                    task.task_id,
                    TaskState.PLANNED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"task {task.task_id} is not in planned state")
            if certificate is not None:
                self.connection.execute(
                    "INSERT INTO certificates(certificate_id,campaign_id,task_id,sha256,payload_json) VALUES(?,?,?,?,?)",
                    (certificate_id, self.campaign_id_for_task(task.task_id), task.task_id, certificate_sha, _json(certificate)),
                )
            self._event(
                self.campaign_id_for_task(task.task_id),
                task.task_id,
                "task_transition",
                {"state": state.value, "factor": factor, "certificate_id": certificate_id, "error": error},
            )

    def campaign_id_for_task(self, task_id: str) -> str:
        row = self.connection.execute("SELECT campaign_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return str(row[0])

    def checkpoint(self, campaign_id: str) -> dict[str, Any]:
        rows = self.connection.execute(
            "SELECT state, COUNT(*) AS count FROM tasks WHERE campaign_id=? GROUP BY state ORDER BY state",
            (campaign_id,),
        ).fetchall()
        counts = {str(row["state"]): int(row["count"]) for row in rows}
        last = self.connection.execute(
            "SELECT MAX(ordinal) FROM tasks WHERE campaign_id=? AND state<>?",
            (campaign_id, TaskState.PLANNED.value),
        ).fetchone()[0]
        return {
            "campaign_id": campaign_id,
            "state_counts": counts,
            "last_processed_ordinal": None if last is None else int(last),
            "pending": counts.get(TaskState.PLANNED.value, 0),
        }

    def certificate_payloads(self, campaign_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload_json FROM certificates WHERE campaign_id=? ORDER BY task_id", (campaign_id,)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def event_count(self, campaign_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM events WHERE campaign_id=?", (campaign_id,)
        ).fetchone()
        return int(row[0])

    def integrity_check(self) -> bool:
        return self.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
