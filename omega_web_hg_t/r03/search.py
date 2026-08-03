from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Mapping

from .models import ClaimCandidate

_TOKEN = re.compile(r"[\wÀ-ÖØ-öø-ÿ'-]+", flags=re.UNICODE)


class SearchIndex:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.fts_enabled = self._create_schema()

    def _create_schema(self) -> bool:
        self.connection.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                url TEXT NOT NULL,
                locator TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind);
            CREATE INDEX IF NOT EXISTS idx_documents_evidence ON documents(evidence_id);
        """)
        try:
            self.connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(document_id UNINDEXED, title, text, content='documents', content_rowid='rowid')")
            self.connection.executescript("""
                CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                  INSERT INTO documents_fts(rowid, document_id, title, text) VALUES (new.rowid, new.document_id, new.title, new.text);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                  INSERT INTO documents_fts(documents_fts, rowid, document_id, title, text) VALUES('delete', old.rowid, old.document_id, old.title, old.text);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                  INSERT INTO documents_fts(documents_fts, rowid, document_id, title, text) VALUES('delete', old.rowid, old.document_id, old.title, old.text);
                  INSERT INTO documents_fts(rowid, document_id, title, text) VALUES (new.rowid, new.document_id, new.title, new.text);
                END;
            """)
            self.connection.commit()
            return True
        except sqlite3.OperationalError:
            self.connection.commit()
            return False

    def add_document(
        self,
        *,
        document_id: str,
        kind: str,
        title: str,
        text: str,
        url: str,
        locator: str,
        evidence_id: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO documents(document_id, kind, title, text, url, locator, evidence_id, metadata_json)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (document_id, kind, title, text, url, locator, evidence_id, json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)),
        )

    def build(
        self,
        *,
        pages: Iterable[Mapping[str, object]],
        sections: Iterable[Mapping[str, object]],
        claims: Iterable[ClaimCandidate],
    ) -> None:
        page_map = {str(item["page_id"]): item for item in pages}
        for page in page_map.values():
            self.add_document(
                document_id=str(page["page_id"]),
                kind="page",
                title=str(page.get("title") or page.get("canonical_url") or ""),
                text=str(page.get("title") or ""),
                url=str(page.get("canonical_url") or page.get("final_url") or ""),
                locator="page",
                evidence_id=str(page.get("evidence_id") or ""),
                metadata=page,
            )
        for section in sections:
            page = page_map.get(str(section["page_id"]), {})
            self.add_document(
                document_id=str(section["section_id"]),
                kind="section",
                title=str(section.get("heading") or "Section"),
                text=str(section.get("text") or ""),
                url=str(page.get("canonical_url") or page.get("final_url") or ""),
                locator=str(section.get("locator") or ""),
                evidence_id=str(page.get("evidence_id") or ""),
                metadata=section,
            )
        for claim in claims:
            self.add_document(
                document_id=claim.claim_id,
                kind="claim_candidate",
                title="Claim candidate",
                text=claim.text,
                url=claim.url,
                locator=claim.locator,
                evidence_id=claim.evidence_id,
                metadata=asdict(claim),
            )
        self.connection.commit()
        if self.fts_enabled:
            self.connection.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
            self.connection.commit()

    @staticmethod
    def _fts_query(query: str) -> str:
        tokens = [token.replace('"', "") for token in _TOKEN.findall(query)]
        if not tokens:
            raise ValueError("Search query must contain at least one word")
        return " AND ".join(f'"{token}"' for token in tokens)

    def query(self, query: str, *, limit: int = 20, kinds: tuple[str, ...] = ()) -> list[dict[str, object]]:
        if limit <= 0:
            raise ValueError("limit must be > 0")
        parameters: list[object] = []
        kind_clause = ""
        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            kind_clause = f" AND d.kind IN ({placeholders})"
        if self.fts_enabled:
            sql = f"""
                SELECT d.*, bm25(documents_fts, 2.0, 1.0) AS score
                FROM documents_fts
                JOIN documents d ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?{kind_clause}
                ORDER BY score ASC, d.document_id ASC
                LIMIT ?
            """
            parameters.append(self._fts_query(query))
            parameters.extend(kinds)
            parameters.append(limit)
        else:
            sql = f"""
                SELECT d.*, 0.0 AS score
                FROM documents d
                WHERE (lower(d.title) LIKE ? OR lower(d.text) LIKE ?){kind_clause}
                ORDER BY d.document_id ASC
                LIMIT ?
            """
            pattern = f"%{query.casefold()}%"
            parameters.extend([pattern, pattern])
            parameters.extend(kinds)
            parameters.append(limit)
        rows = self.connection.execute(sql, parameters).fetchall()
        return [
            {
                "document_id": row["document_id"],
                "kind": row["kind"],
                "title": row["title"],
                "text": row["text"],
                "url": row["url"],
                "locator": row["locator"],
                "evidence_id": row["evidence_id"],
                "score": float(row["score"]),
                "metadata": json.loads(row["metadata_json"]),
            }
            for row in rows
        ]

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SearchIndex":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
