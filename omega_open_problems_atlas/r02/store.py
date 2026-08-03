"""Durable SQLite store for atlas R0.2.

The store is append/audit oriented. It contains public research metadata only;
credentials, private correspondence, bank data and identity documents are
outside its schema by construction.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator

from .merkle import merkle_root
from .models import EvidenceReceipt, MethodCard, ProblemLead, ProofObligation, TransferEdge


SCHEMA_VERSION = 2
EXPECTED_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "metadata": ("key", "value"),
    "leads": (
        "lead_id",
        "source_id",
        "statement_hash",
        "canonical_hash",
        "status",
        "independently_checked_open",
        "solution_claimed",
        "payload",
    ),
    "methods": ("method_id", "canonical_hash", "payload"),
    "obligations": (
        "obligation_id",
        "problem_id",
        "canonical_hash",
        "status",
        "finite_budget_units",
        "universal_claim",
        "payload",
    ),
    "transfer_edges": (
        "edge_id",
        "source_problem_id",
        "target_problem_id",
        "method_id",
        "validated",
        "canonical_hash",
        "payload",
    ),
    "receipts": (
        "receipt_id",
        "subject_id",
        "receipt_hash",
        "parent_receipt_hash",
        "payload",
    ),
    "m_minus": (
        "entry_id",
        "subject_id",
        "failure_class",
        "observation",
        "created_at",
    ),
    "checkpoints": (
        "checkpoint_id",
        "created_at",
        "lead_count",
        "method_count",
        "obligation_count",
        "edge_count",
        "receipt_count",
        "merkle_root",
    ),
}


class AtlasStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "AtlasStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS leads(
                lead_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                statement_hash TEXT NOT NULL,
                canonical_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                independently_checked_open INTEGER NOT NULL CHECK(independently_checked_open IN (0,1)),
                solution_claimed INTEGER NOT NULL CHECK(solution_claimed IN (0,1)),
                payload TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS leads_source_locator
                ON leads(source_id, json_extract(payload, '$.source_locator'));
            CREATE INDEX IF NOT EXISTS leads_statement_hash ON leads(statement_hash);
            CREATE TABLE IF NOT EXISTS methods(
                method_id TEXT PRIMARY KEY,
                canonical_hash TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS obligations(
                obligation_id TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                canonical_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                finite_budget_units INTEGER NOT NULL CHECK(finite_budget_units > 0),
                universal_claim INTEGER NOT NULL CHECK(universal_claim IN (0,1)),
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS obligations_problem_id ON obligations(problem_id);
            CREATE TABLE IF NOT EXISTS transfer_edges(
                edge_id TEXT PRIMARY KEY,
                source_problem_id TEXT NOT NULL,
                target_problem_id TEXT NOT NULL,
                method_id TEXT NOT NULL,
                validated INTEGER NOT NULL CHECK(validated IN (0,1)),
                canonical_hash TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS receipts(
                receipt_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                receipt_hash TEXT NOT NULL,
                parent_receipt_hash TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS m_minus(
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id TEXT NOT NULL,
                failure_class TEXT NOT NULL,
                observation TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints(
                checkpoint_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                lead_count INTEGER NOT NULL,
                method_count INTEGER NOT NULL,
                obligation_count INTEGER NOT NULL,
                edge_count INTEGER NOT NULL,
                receipt_count INTEGER NOT NULL,
                merkle_root TEXT NOT NULL
            );
            """
        )
        self.validate_schema_contract()
        self.connection.execute(
            "INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.connection.commit()

    @staticmethod
    def _json(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def table_columns(self, table: str) -> tuple[str, ...]:
        if table not in EXPECTED_TABLE_COLUMNS:
            raise ValueError(f"unsupported schema table: {table}")
        rows = self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        return tuple(str(row["name"]) for row in rows)

    def validate_schema_contract(self) -> dict[str, tuple[str, ...]]:
        observed = {
            table: self.table_columns(table)
            for table in EXPECTED_TABLE_COLUMNS
        }
        mismatches = {
            table: {"expected": EXPECTED_TABLE_COLUMNS[table], "observed": columns}
            for table, columns in observed.items()
            if columns != EXPECTED_TABLE_COLUMNS[table]
        }
        if mismatches:
            raise RuntimeError(f"SQLite schema contract mismatch: {mismatches}")
        return observed

    def upsert_lead(self, lead: ProblemLead) -> None:
        payload = asdict(lead)
        payload["lead_status"] = lead.lead_status.value
        self.connection.execute(
            """INSERT INTO leads(
                   lead_id,
                   source_id,
                   statement_hash,
                   canonical_hash,
                   status,
                   independently_checked_open,
                   solution_claimed,
                   payload
               ) VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(lead_id) DO UPDATE SET
                 source_id=excluded.source_id,
                 statement_hash=excluded.statement_hash,
                 canonical_hash=excluded.canonical_hash,
                 status=excluded.status,
                 independently_checked_open=excluded.independently_checked_open,
                 solution_claimed=excluded.solution_claimed,
                 payload=excluded.payload""",
            (
                lead.lead_id,
                lead.source_id,
                lead.statement_hash(),
                lead.canonical_hash(),
                lead.lead_status.value,
                int(lead.independently_checked_open),
                int(lead.solution_claimed),
                self._json(payload),
            ),
        )

    def upsert_method(self, method: MethodCard) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO methods VALUES(?,?,?)",
            (method.method_id, method.canonical_hash(), self._json(asdict(method))),
        )

    def upsert_obligation(self, obligation: ProofObligation) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO obligations VALUES(?,?,?,?,?,?,?)",
            (
                obligation.obligation_id,
                obligation.problem_id,
                obligation.canonical_hash(),
                obligation.status.value,
                obligation.finite_budget_units,
                int(obligation.universal_claim),
                self._json(obligation.canonical_payload()),
            ),
        )

    def upsert_edge(self, edge: TransferEdge) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO transfer_edges VALUES(?,?,?,?,?,?,?)",
            (
                edge.edge_id,
                edge.source_problem_id,
                edge.target_problem_id,
                edge.method_id,
                int(edge.transfer_validated),
                edge.canonical_hash(),
                self._json(asdict(edge)),
            ),
        )

    def append_receipt(self, receipt: EvidenceReceipt) -> None:
        self.connection.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?)",
            (
                receipt.receipt_id,
                receipt.subject_id,
                receipt.canonical_hash(),
                receipt.parent_receipt_hash,
                self._json(receipt.canonical_payload()),
            ),
        )

    def append_m_minus(self, subject_id: str, failure_class: str, observation: str, created_at: str) -> None:
        self.connection.execute(
            "INSERT INTO m_minus(subject_id,failure_class,observation,created_at) VALUES(?,?,?,?)",
            (subject_id, failure_class, observation, created_at),
        )

    def insert_leads(self, leads: Iterable[ProblemLead], batch_size: int = 1000) -> int:
        count = 0
        with self.transaction():
            for lead in leads:
                self.upsert_lead(lead)
                count += 1
                if count % batch_size == 0:
                    self.connection.commit()
                    self.connection.execute("BEGIN IMMEDIATE")
        return count

    def insert_obligations(self, obligations: Iterable[ProofObligation], batch_size: int = 2000) -> int:
        count = 0
        with self.transaction():
            for obligation in obligations:
                self.upsert_obligation(obligation)
                count += 1
                if count % batch_size == 0:
                    self.connection.commit()
                    self.connection.execute("BEGIN IMMEDIATE")
        return count

    def count(self, table: str) -> int:
        allowed = {"leads", "methods", "obligations", "transfer_edges", "receipts", "m_minus"}
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        return int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def independently_checked_open_count(self) -> int:
        return int(
            self.connection.execute(
                "SELECT COUNT(*) FROM leads WHERE independently_checked_open=1"
            ).fetchone()[0]
        )

    def solution_claim_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM leads WHERE solution_claimed=1").fetchone()[0])

    def hashes(self) -> list[str]:
        rows: list[str] = []
        for table, column in (
            ("leads", "canonical_hash"),
            ("methods", "canonical_hash"),
            ("obligations", "canonical_hash"),
            ("transfer_edges", "canonical_hash"),
            ("receipts", "receipt_hash"),
        ):
            rows.extend(
                row[0]
                for row in self.connection.execute(
                    f"SELECT {column} FROM {table} ORDER BY 1"
                ).fetchall()
            )
        return rows

    def checkpoint(self, checkpoint_id: str, created_at: str) -> dict[str, object]:
        payload = {
            "checkpoint_id": checkpoint_id,
            "created_at": created_at,
            "lead_count": self.count("leads"),
            "method_count": self.count("methods"),
            "obligation_count": self.count("obligations"),
            "edge_count": self.count("transfer_edges"),
            "receipt_count": self.count("receipts"),
            "merkle_root": merkle_root(self.hashes()),
        }
        self.connection.execute(
            "INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,?,?,?,?,?)",
            (
                payload["checkpoint_id"],
                payload["created_at"],
                payload["lead_count"],
                payload["method_count"],
                payload["obligation_count"],
                payload["edge_count"],
                payload["receipt_count"],
                payload["merkle_root"],
            ),
        )
        self.connection.commit()
        return payload
