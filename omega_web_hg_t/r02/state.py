from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from omega_web_hg_t.models import utc_now
from .models import ChangeRecord, FrontierItem, VersionRecord


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, seed_url TEXT NOT NULL, config_sha256 TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS frontier (url TEXT PRIMARY KEY, depth INTEGER NOT NULL, priority REAL NOT NULL, discovered_from TEXT, mechanism TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0, queued_at TEXT NOT NULL, lease_until TEXT);
            CREATE TABLE IF NOT EXISTS url_state (url TEXT PRIMARY KEY, canonical_url TEXT, etag TEXT, last_modified TEXT, content_sha256 TEXT, version_id TEXT, evidence_id TEXT, last_status INTEGER, last_fetched_at TEXT, error_count INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS versions (version_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, url TEXT NOT NULL, fetched_at TEXT NOT NULL, content_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_versions_url_time ON versions(url, fetched_at DESC);
            CREATE TABLE IF NOT EXISTS changes (change_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, url TEXT NOT NULL, detected_at TEXT NOT NULL, change_type TEXT NOT NULL, payload_json TEXT NOT NULL);
        """)
        self.connection.commit()

    def start_run(self, run_id: str, *, seed_url: str, config_sha256: str) -> bool:
        existed = self.connection.execute("SELECT 1 FROM runs LIMIT 1").fetchone() is not None
        self.connection.execute("INSERT OR REPLACE INTO runs(run_id, seed_url, config_sha256, started_at, status) VALUES(?,?,?,?,?)", (run_id, seed_url, config_sha256, utc_now(), "running"))
        self.connection.commit()
        return existed

    def finish_run(self, run_id: str, status: str) -> None:
        self.connection.execute("UPDATE runs SET finished_at=?, status=? WHERE run_id=?", (utc_now(), status, run_id))
        self.connection.commit()

    def enqueue(self, url: str, *, depth: int, priority: float = 0.0, discovered_from: str | None = None, mechanism: str = "link") -> bool:
        cursor = self.connection.execute("INSERT OR IGNORE INTO frontier(url, depth, priority, discovered_from, mechanism, state, queued_at) VALUES(?,?,?,?,?,'queued',?)", (url, depth, priority, discovered_from, mechanism, utc_now()))
        self.connection.commit()
        return cursor.rowcount > 0

    def recover_leases(self) -> int:
        cursor = self.connection.execute("UPDATE frontier SET state='queued', lease_until=NULL WHERE state='leased' AND lease_until < ?", (utc_now(),))
        self.connection.commit()
        return cursor.rowcount

    def claim_next(self, *, lease_until: str) -> FrontierItem | None:
        self.recover_leases()
        row = self.connection.execute("SELECT url, depth, priority, discovered_from, mechanism, attempts FROM frontier WHERE state='queued' ORDER BY priority DESC, depth ASC, queued_at ASC LIMIT 1").fetchone()
        if row is None:
            return None
        self.connection.execute("UPDATE frontier SET state='leased', lease_until=?, attempts=attempts+1 WHERE url=?", (lease_until, row["url"]))
        self.connection.commit()
        return FrontierItem(url=row["url"], depth=int(row["depth"]), priority=float(row["priority"]), discovered_from=row["discovered_from"], mechanism=row["mechanism"], attempts=int(row["attempts"]) + 1)

    def complete(self, url: str) -> None:
        self.connection.execute("DELETE FROM frontier WHERE url=?", (url,))
        self.connection.commit()

    def requeue(self, url: str) -> None:
        self.connection.execute("UPDATE frontier SET state='queued', lease_until=NULL, queued_at=? WHERE url=?", (utc_now(), url))
        self.connection.commit()

    def frontier_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM frontier").fetchone()
        return int(row["count"])

    def known_urls(self) -> list[str]:
        rows = self.connection.execute("SELECT url FROM url_state ORDER BY url").fetchall()
        return [str(row["url"]) for row in rows]

    def conditional_headers(self, url: str) -> dict[str, str]:
        row = self.connection.execute("SELECT etag, last_modified FROM url_state WHERE url=?", (url,)).fetchone()
        if row is None:
            return {}
        headers: dict[str, str] = {}
        if row["etag"]:
            headers["If-None-Match"] = str(row["etag"])
        if row["last_modified"]:
            headers["If-Modified-Since"] = str(row["last_modified"])
        return headers

    def latest_version(self, url: str) -> VersionRecord | None:
        row = self.connection.execute("SELECT payload_json FROM versions WHERE url=? ORDER BY fetched_at DESC LIMIT 1", (url,)).fetchone()
        if row is None:
            return None
        return VersionRecord(**json.loads(row["payload_json"]))

    def record_version(self, version: VersionRecord) -> None:
        payload = json.dumps(asdict(version), ensure_ascii=False, sort_keys=True)
        self.connection.execute("INSERT OR REPLACE INTO versions(version_id, run_id, url, fetched_at, content_sha256, payload_json) VALUES(?,?,?,?,?,?)", (version.version_id, version.run_id, version.url, version.fetched_at, version.content_sha256, payload))
        self.connection.execute("""
            INSERT INTO url_state(url, canonical_url, etag, last_modified, content_sha256, version_id, evidence_id, last_status, last_fetched_at, error_count)
            VALUES(?,?,?,?,?,?,?,?,?,0)
            ON CONFLICT(url) DO UPDATE SET canonical_url=excluded.canonical_url, etag=excluded.etag, last_modified=excluded.last_modified, content_sha256=excluded.content_sha256, version_id=excluded.version_id, evidence_id=excluded.evidence_id, last_status=excluded.last_status, last_fetched_at=excluded.last_fetched_at, error_count=0
        """, (version.url, version.canonical_url, version.etag, version.last_modified, version.content_sha256, version.version_id, version.evidence_id, version.http_status, version.fetched_at))
        self.connection.commit()

    def record_not_modified(self, url: str, *, status: int = 304) -> None:
        self.connection.execute("UPDATE url_state SET last_status=?, last_fetched_at=?, error_count=0 WHERE url=?", (status, utc_now(), url))
        self.connection.commit()

    def record_error(self, url: str) -> None:
        self.connection.execute("INSERT INTO url_state(url, error_count, last_fetched_at) VALUES(?,1,?) ON CONFLICT(url) DO UPDATE SET error_count=error_count+1, last_fetched_at=excluded.last_fetched_at", (url, utc_now()))
        self.connection.commit()

    def record_change(self, change: ChangeRecord) -> None:
        payload = json.dumps(asdict(change), ensure_ascii=False, sort_keys=True)
        self.connection.execute("INSERT OR REPLACE INTO changes(change_id, run_id, url, detected_at, change_type, payload_json) VALUES(?,?,?,?,?,?)", (change.change_id, change.run_id, change.url, change.detected_at, change.change_type, payload))
        self.connection.commit()

    def stats(self) -> dict[str, int]:
        result = {}
        for table in ("runs", "frontier", "url_state", "versions", "changes"):
            row = self.connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
            result[table] = int(row["count"])
        return result

    def snapshot(self, destination: str | Path) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target_connection = sqlite3.connect(target)
        with target_connection:
            self.connection.backup(target_connection)
        target_connection.close()
        return target

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "StateStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
