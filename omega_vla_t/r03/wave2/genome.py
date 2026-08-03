"""Operator genomes and persistent content-addressed registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping

from ..types import MathType, math_type_from_dict
from .properties import PropertyEvidence


class GenomeError(ValueError):
    pass


@dataclass(frozen=True)
class OperatorGenome:
    genome_id: str
    family_id: str
    name: str
    math_type: MathType
    representation: str
    parameters: tuple[tuple[str, str], ...] = ()
    assumptions: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    algorithms: tuple[str, ...] = ()
    backends: tuple[str, ...] = ()
    property_evidence: tuple[PropertyEvidence, ...] = ()
    residuals: tuple[tuple[str, float], ...] = ()
    provenance: tuple[str, ...] = ()
    status: str = "defined"
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.genome_id.strip() or not self.family_id.strip() or not self.name.strip():
            raise GenomeError("genome_id, family_id and name are required")
        if self.representation not in {
            "symbolic",
            "dense",
            "csr",
            "matrix_free",
            "tensor",
            "graph",
            "formal_target",
            "hybrid",
        }:
            raise GenomeError("unsupported operator representation")
        if self.status not in {
            "idea",
            "defined",
            "implemented",
            "tested",
            "refuted",
            "formalized_incomplete",
            "formally_verified",
            "canonical",
        }:
            raise GenomeError("invalid operator genome status")
        if self.theorem_claimed and self.status not in {"formally_verified", "canonical"}:
            raise GenomeError("theorem claims require proof-level status")
        keys = [key for key, _ in self.parameters]
        if len(keys) != len(set(keys)):
            raise GenomeError("genome parameter keys must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "family_id": self.family_id,
            "name": self.name,
            "math_type": self.math_type.to_dict(),
            "representation": self.representation,
            "parameters": dict(self.parameters),
            "assumptions": list(self.assumptions),
            "invariants": list(self.invariants),
            "algorithms": list(self.algorithms),
            "backends": list(self.backends),
            "property_evidence": [value.to_dict() for value in self.property_evidence],
            "residuals": dict(self.residuals),
            "provenance": list(self.provenance),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OperatorGenome":
        evidence = []
        from .properties import EvidenceLevel
        for item in payload.get("property_evidence", []):
            evidence.append(
                PropertyEvidence(
                    property_name=str(item["property_name"]),
                    supported=item.get("supported"),
                    evidence_level=EvidenceLevel(str(item["evidence_level"])),
                    residual=item.get("residual"),
                    threshold=item.get("threshold"),
                    method=str(item["method"]),
                    assumptions=tuple(item.get("assumptions", ())),
                    witnesses=tuple(item.get("witnesses", ())),
                    theorem_claimed=bool(item.get("theorem_claimed", False)),
                    formal_proof_claimed=bool(item.get("formal_proof_claimed", False)),
                )
            )
        return cls(
            genome_id=str(payload["genome_id"]),
            family_id=str(payload["family_id"]),
            name=str(payload["name"]),
            math_type=math_type_from_dict(payload["math_type"]),
            representation=str(payload["representation"]),
            parameters=tuple(sorted((str(k), str(v)) for k, v in payload.get("parameters", {}).items())),
            assumptions=tuple(payload.get("assumptions", ())),
            invariants=tuple(payload.get("invariants", ())),
            algorithms=tuple(payload.get("algorithms", ())),
            backends=tuple(payload.get("backends", ())),
            property_evidence=tuple(evidence),
            residuals=tuple(sorted((str(k), float(v)) for k, v in payload.get("residuals", {}).items())),
            provenance=tuple(payload.get("provenance", ())),
            status=str(payload.get("status", "defined")),
            theorem_claimed=bool(payload.get("theorem_claimed", False)),
            formal_proof_claimed=bool(payload.get("formal_proof_claimed", False)),
            scientific_validation_claimed=bool(payload.get("scientific_validation_claimed", False)),
        )


class OperatorGenomeRegistry:
    """SQLite-backed exact registry with family and status indexes."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS genomes (
                digest TEXT PRIMARY KEY,
                genome_id TEXT NOT NULL,
                family_id TEXT NOT NULL,
                status TEXT NOT NULL,
                representation TEXT NOT NULL,
                payload TEXT NOT NULL
            ) WITHOUT ROWID
            """
        )
        self.connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS genomes_genome_id ON genomes(genome_id)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS genomes_family ON genomes(family_id)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS genomes_status ON genomes(status)"
        )

    def __enter__(self) -> "OperatorGenomeRegistry":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.close()

    def add(self, genome: OperatorGenome, *, replace: bool = False) -> tuple[bool, str]:
        digest = genome.digest()
        payload = genome.canonical_json()
        if replace:
            self.connection.execute("DELETE FROM genomes WHERE genome_id = ?", (genome.genome_id,))
        try:
            cursor = self.connection.execute(
                """
                INSERT INTO genomes(digest, genome_id, family_id, status, representation, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    digest,
                    genome.genome_id,
                    genome.family_id,
                    genome.status,
                    genome.representation,
                    payload,
                ),
            )
        except sqlite3.IntegrityError as exc:
            existing = self.connection.execute(
                "SELECT digest FROM genomes WHERE genome_id = ? OR digest = ? LIMIT 1",
                (genome.genome_id, digest),
            ).fetchone()
            if existing and existing[0] == digest:
                return False, digest
            raise GenomeError("genome_id already refers to different content") from exc
        return cursor.rowcount == 1, digest

    def get(self, genome_id: str) -> OperatorGenome:
        row = self.connection.execute(
            "SELECT payload FROM genomes WHERE genome_id = ?", (genome_id,)
        ).fetchone()
        if row is None:
            raise GenomeError(f"unknown genome_id: {genome_id}")
        return OperatorGenome.from_dict(json.loads(row[0]))

    def by_family(self, family_id: str) -> tuple[OperatorGenome, ...]:
        rows = self.connection.execute(
            "SELECT payload FROM genomes WHERE family_id = ? ORDER BY genome_id",
            (family_id,),
        ).fetchall()
        return tuple(OperatorGenome.from_dict(json.loads(row[0])) for row in rows)

    def by_status(self, status: str) -> tuple[OperatorGenome, ...]:
        rows = self.connection.execute(
            "SELECT payload FROM genomes WHERE status = ? ORDER BY genome_id",
            (status,),
        ).fetchall()
        return tuple(OperatorGenome.from_dict(json.loads(row[0])) for row in rows)

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM genomes").fetchone()
        return int(row[0])

    def summary(self) -> dict[str, Any]:
        family_count = int(
            self.connection.execute("SELECT COUNT(DISTINCT family_id) FROM genomes").fetchone()[0]
        )
        statuses = {
            status: int(count)
            for status, count in self.connection.execute(
                "SELECT status, COUNT(*) FROM genomes GROUP BY status ORDER BY status"
            ).fetchall()
        }
        representations = {
            representation: int(count)
            for representation, count in self.connection.execute(
                "SELECT representation, COUNT(*) FROM genomes GROUP BY representation ORDER BY representation"
            ).fetchall()
        }
        return {
            "genomes": self.count(),
            "families": family_count,
            "statuses": statuses,
            "representations": representations,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }

    def export_jsonl(self, path: str | Path) -> str:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute(
            "SELECT payload FROM genomes ORDER BY genome_id"
        ).fetchall()
        content = "".join(row[0] + "\n" for row in rows)
        destination.write_text(content, encoding="utf-8")
        return sha256(content.encode("utf-8")).hexdigest()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()
