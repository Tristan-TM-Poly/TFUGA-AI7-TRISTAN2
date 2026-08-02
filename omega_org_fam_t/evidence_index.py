"""SQLite evidence index with explicit provenance and family-score queries."""
from __future__ import annotations

from contextlib import AbstractContextManager
import json
from pathlib import Path
import sqlite3
from typing import Mapping

from .evidence_models import EvidenceBundle


class EvidenceIndex(AbstractContextManager["EvidenceIndex"]):
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS bundles(
              bundle_id TEXT PRIMARY KEY,
              formula TEXT,
              charge INTEGER NOT NULL,
              status TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources(
              source_id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              locator TEXT NOT NULL,
              license TEXT NOT NULL,
              quality REAL NOT NULL,
              content_sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations(
              observation_id TEXT PRIMARY KEY,
              bundle_id TEXT NOT NULL REFERENCES bundles(bundle_id) ON DELETE CASCADE,
              modality TEXT NOT NULL,
              source_id TEXT NOT NULL REFERENCES sources(source_id),
              peak_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS family_scores(
              bundle_id TEXT NOT NULL REFERENCES bundles(bundle_id) ON DELETE CASCADE,
              family TEXT NOT NULL,
              score REAL NOT NULL,
              status TEXT NOT NULL,
              modalities INTEGER NOT NULL,
              contradictions INTEGER NOT NULL,
              PRIMARY KEY(bundle_id, family)
            );
            CREATE INDEX IF NOT EXISTS idx_family_score ON family_scores(family, score DESC);
            CREATE INDEX IF NOT EXISTS idx_observation_modality ON observations(modality);
            """
        )
        self.connection.commit()

    def ingest_bundle(self, bundle: EvidenceBundle) -> None:
        source_map = bundle.source_map()
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO bundles VALUES(?,?,?,?,?)",
                (bundle.bundle_id, bundle.formula, bundle.charge, bundle.status, json.dumps(bundle.to_dict(), sort_keys=True)),
            )
            for source in source_map.values():
                self.connection.execute(
                    "INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)",
                    (source.source_id, source.title, source.locator, source.license, source.quality, source.content_sha256),
                )
            for observation in bundle.observations:
                self.connection.execute(
                    "INSERT OR REPLACE INTO observations VALUES(?,?,?,?,?)",
                    (observation.observation_id, bundle.bundle_id, observation.modality, observation.source_id, len(observation.peaks)),
                )

    def upsert_family_scores(self, bundle_id: str, scores: Mapping[str, Mapping[str, object]]) -> None:
        with self.connection:
            for family, result in scores.items():
                self.connection.execute(
                    "INSERT OR REPLACE INTO family_scores VALUES(?,?,?,?,?,?)",
                    (
                        bundle_id,
                        family,
                        float(result.get("score", 0.0)),
                        str(result.get("status", "unknown")),
                        int(result.get("modalities", 0)),
                        int(result.get("contradictions", 0)),
                    ),
                )

    def query_family(self, family: str, *, minimum_score: float = 0.0, limit: int = 100) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT family_scores.*, bundles.formula, bundles.status AS bundle_status
               FROM family_scores JOIN bundles USING(bundle_id)
               WHERE family=? AND score>=? ORDER BY score DESC, bundle_id LIMIT ?""",
            (family, minimum_score, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict[str, int]:
        return {
            table: int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("bundles", "sources", "observations", "family_scores")
        }

    def close(self) -> None:
        self.connection.close()

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
