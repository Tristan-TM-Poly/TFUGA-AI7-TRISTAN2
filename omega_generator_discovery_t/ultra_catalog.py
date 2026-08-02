"""Streaming and partitioned SQLite access for Ω-GENERATOR-DISCOVERY R0.3 Ultra.

This module queries generated research candidates. It never promotes a candidate
into a physical law or empirical result. All result sets remain subject to OAK
review, provenance, units, uncertainty, baselines and falsification.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Mapping, Sequence


DEFAULT_ROOT = Path("generated/omega_generator_discovery_r03_ultra")


@dataclass(frozen=True, slots=True)
class UltraGeneratorRecord:
    id: str
    ordinal: int
    domain: str
    family: str
    scale: str
    representation: str
    regime: str
    status: str
    invariant: str
    risk: str
    risk_tier: str
    supports_inverse: bool
    operator_dsl: str
    payload: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["payload"] = dict(self.payload)
        return result


@dataclass(frozen=True, slots=True)
class UltraAuditReport:
    valid: bool
    counts: Mapping[str, int]
    expected: Mapping[str, int]
    orphan_benchmarks: int
    orphan_hyperedges: int
    missing_negative_controls: int
    missing_validations: int
    high_risk_not_exhaustive: int
    duplicate_coordinate_groups: int
    combined_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "counts": dict(self.counts),
            "expected": dict(self.expected),
            "orphan_benchmarks": self.orphan_benchmarks,
            "orphan_hyperedges": self.orphan_hyperedges,
            "missing_negative_controls": self.missing_negative_controls,
            "missing_validations": self.missing_validations,
            "high_risk_not_exhaustive": self.high_risk_not_exhaustive,
            "duplicate_coordinate_groups": self.duplicate_coordinate_groups,
            "combined_fingerprint": self.combined_fingerprint,
        }


def load_manifest(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    path = root / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"Ultra manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_name(domain: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in domain)


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    atlas_relative = root / path
    if atlas_relative.exists():
        return atlas_relative
    # Backward compatibility with manifests that stored repository-relative paths.
    if len(root.parents) >= 2:
        repository_relative = root.parents[1] / path
        if repository_relative.exists():
            return repository_relative
    return atlas_relative


def _database_config(root: Path) -> str | dict[str, object]:
    value = load_manifest(root).get("database")
    if isinstance(value, (str, dict)):
        return value
    # Fallback for an atlas generated before the manifest gained a database field.
    return "index/omega_generator_r03_ultra.sqlite3"


def _is_partitioned(root: Path) -> bool:
    config = _database_config(root)
    return isinstance(config, dict) and config.get("mode") == "partitioned_by_domain"


def _routing_database(root: Path) -> Path:
    config = _database_config(root)
    if isinstance(config, dict):
        return _resolve_path(root, str(config["routing"]))
    return _resolve_path(root, config)


def _domain_database(root: Path, domain: str) -> Path:
    if _is_partitioned(root):
        path = root / "index" / "domains" / f"{_safe_name(domain)}.sqlite3"
        if not path.exists():
            raise KeyError(f"Unknown or missing domain partition: {domain}")
        return path
    return _routing_database(root)


def _partition_paths(root: Path) -> tuple[Path, ...]:
    config = _database_config(root)
    if isinstance(config, dict) and config.get("mode") == "partitioned_by_domain":
        return tuple(_resolve_path(root, str(value)) for value in config["partitions"])
    return (_routing_database(root),)


def _connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _row_to_generator(row: sqlite3.Row) -> UltraGeneratorRecord:
    payload = json.loads(row["payload"])
    return UltraGeneratorRecord(
        id=row["id"],
        ordinal=int(row["ordinal"]),
        domain=row["domain"],
        family=row["family"],
        scale=row["scale"],
        representation=row["representation"],
        regime=row["regime"],
        status=row["status"],
        invariant=row["invariant_name"],
        risk=row["risk"],
        risk_tier=row["risk_tier"],
        supports_inverse=bool(row["supports_inverse"]),
        operator_dsl=str(payload["operator_dsl"]),
        payload=payload,
    )


def _fetch_records_by_ids(root: Path, routing_rows: Sequence[sqlite3.Row]) -> tuple[UltraGeneratorRecord, ...]:
    if not routing_rows:
        return ()
    if "payload" in routing_rows[0].keys():
        return tuple(_row_to_generator(row) for row in routing_rows)

    ids_by_domain: dict[str, list[str]] = defaultdict(list)
    ordered_ids: list[str] = []
    for row in routing_rows:
        generator_id = str(row["id"])
        ordered_ids.append(generator_id)
        ids_by_domain[str(row["domain"])].append(generator_id)

    records: dict[str, UltraGeneratorRecord] = {}
    for domain, generator_ids in ids_by_domain.items():
        connection = _connect(_domain_database(root, domain))
        try:
            for start in range(0, len(generator_ids), 500):
                chunk = generator_ids[start : start + 500]
                placeholders = ",".join("?" for _ in chunk)
                for row in connection.execute(
                    f"SELECT * FROM generators WHERE id IN ({placeholders})", chunk
                ):
                    record = _row_to_generator(row)
                    records[record.id] = record
        finally:
            connection.close()
    return tuple(records[generator_id] for generator_id in ordered_ids)


def query_generators(
    *,
    root: Path = DEFAULT_ROOT,
    domain: str | None = None,
    family: str | None = None,
    scale: str | None = None,
    representation: str | None = None,
    regime: str | None = None,
    status: str | None = None,
    invariant: str | None = None,
    risk_tier: str | None = None,
    supports_inverse: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[UltraGeneratorRecord, ...]:
    if limit <= 0 or limit > 10000:
        raise ValueError("limit must be between 1 and 10000")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    filters = {
        "domain": domain,
        "family": family,
        "scale": scale,
        "representation": representation,
        "regime": regime,
        "status": status,
        "invariant_name": invariant,
        "risk_tier": risk_tier,
    }
    clauses: list[str] = []
    parameters: list[object] = []
    for column, value in filters.items():
        if value is not None:
            clauses.append(f"{column}=?")
            parameters.append(value)
    if supports_inverse is not None:
        clauses.append("supports_inverse=?")
        parameters.append(int(supports_inverse))
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    sql = "SELECT * FROM generators" + where + " ORDER BY ordinal LIMIT ? OFFSET ?"
    parameters.extend([limit, offset])
    connection = _connect(_routing_database(root))
    try:
        routing_rows = tuple(connection.execute(sql, parameters))
    finally:
        connection.close()
    return _fetch_records_by_ids(root, routing_rows)


def get_generator(generator_id: str, root: Path = DEFAULT_ROOT) -> UltraGeneratorRecord:
    routing = _connect(_routing_database(root))
    try:
        row = routing.execute("SELECT * FROM generators WHERE id=?", (generator_id,)).fetchone()
    finally:
        routing.close()
    if row is None:
        raise KeyError(generator_id)
    return _fetch_records_by_ids(root, (row,))[0]


def related_bundle(generator_id: str, root: Path = DEFAULT_ROOT) -> dict[str, object]:
    routing = _connect(_routing_database(root))
    try:
        route = routing.execute("SELECT domain FROM generators WHERE id=?", (generator_id,)).fetchone()
    finally:
        routing.close()
    if route is None:
        raise KeyError(generator_id)
    connection = _connect(_domain_database(root, str(route["domain"])))
    try:
        generator = connection.execute("SELECT payload FROM generators WHERE id=?", (generator_id,)).fetchone()
        if generator is None:
            raise KeyError(generator_id)
        benchmarks = [
            json.loads(row["payload"])
            for row in connection.execute(
                "SELECT payload FROM benchmarks WHERE generator_id=? ORDER BY id", (generator_id,)
            )
        ]
        edges = [
            json.loads(row["payload"])
            for row in connection.execute(
                "SELECT payload FROM hyperedges WHERE left_id=? OR right_id=? ORDER BY id",
                (generator_id, generator_id),
            )
        ]
        negative = connection.execute(
            "SELECT payload FROM negative_controls WHERE generator_id=?", (generator_id,)
        ).fetchone()
        validation = connection.execute(
            "SELECT payload FROM validations WHERE generator_id=?", (generator_id,)
        ).fetchone()
        return {
            "generator": json.loads(generator["payload"]),
            "benchmarks": benchmarks,
            "hyperedges": edges,
            "negative_control": json.loads(negative["payload"]) if negative else None,
            "validation": json.loads(validation["payload"]) if validation else None,
        }
    finally:
        connection.close()


def catalog_statistics(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    manifest = load_manifest(root)
    counts_raw = manifest["counts"]
    assert isinstance(counts_raw, dict)
    counts = {
        "generators": int(counts_raw["generators"]),
        "benchmarks": int(counts_raw["benchmarks"]),
        "hyperedges": int(counts_raw["hyperedges"]),
        "negative_controls": int(counts_raw["negative_controls"]),
        "validations": int(counts_raw["validations"]),
    }
    connection = _connect(_routing_database(root))
    try:
        distributions = {}
        for column in ("domain", "family", "scale", "representation", "regime", "status", "risk_tier"):
            distributions[column] = dict(
                connection.execute(
                    f"SELECT {column},COUNT(*) FROM generators GROUP BY {column} ORDER BY {column}"
                ).fetchall()
            )
    finally:
        connection.close()
    return {
        "counts": counts,
        "total_records": sum(counts.values()),
        "distributions": distributions,
        "database_mode": "partitioned_by_domain" if _is_partitioned(root) else "monolithic",
        "manifest": manifest,
    }


def deterministic_validation_sample(
    *, root: Path = DEFAULT_ROOT, modulus: int = 16, residue: int = 0,
    include_all_high_risk: bool = True,
) -> tuple[str, ...]:
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    if residue < 0 or residue >= modulus:
        raise ValueError("residue must satisfy 0 <= residue < modulus")
    connection = _connect(_routing_database(root))
    try:
        if include_all_high_risk:
            rows = connection.execute(
                "SELECT id FROM generators WHERE risk_tier='high' OR ordinal % ? = ? ORDER BY ordinal",
                (modulus, residue),
            )
        else:
            rows = connection.execute(
                "SELECT id FROM generators WHERE ordinal % ? = ? ORDER BY ordinal",
                (modulus, residue),
            )
        return tuple(row[0] for row in rows)
    finally:
        connection.close()


def export_subatlas(
    output: Path,
    *,
    root: Path = DEFAULT_ROOT,
    generator_ids: Sequence[str] | None = None,
    domain: str | None = None,
    family: str | None = None,
    limit: int = 1000,
) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if generator_ids is None:
        selected = query_generators(root=root, domain=domain, family=family, limit=limit)
        generator_ids = [record.id for record in selected]
    digest = hashlib.sha256()
    count = 0
    with output.open("w", encoding="utf-8") as handle:
        for generator_id in generator_ids:
            bundle = related_bundle(generator_id, root)
            line = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False)
            handle.write(line + "\n")
            digest.update(line.encode("utf-8"))
            count += 1
    return {
        "output": str(output),
        "bundles": count,
        "sha256": digest.hexdigest(),
        "epistemic_status": "exported_candidate_subatlas_not_empirical_evidence",
    }


def _audit_connection(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "generators": connection.execute("SELECT COUNT(*) FROM generators").fetchone()[0],
        "benchmarks": connection.execute("SELECT COUNT(*) FROM benchmarks").fetchone()[0],
        "hyperedges": connection.execute("SELECT COUNT(*) FROM hyperedges").fetchone()[0],
        "negative_controls": connection.execute("SELECT COUNT(*) FROM negative_controls").fetchone()[0],
        "validations": connection.execute("SELECT COUNT(*) FROM validations").fetchone()[0],
        "orphan_benchmarks": connection.execute(
            "SELECT COUNT(*) FROM benchmarks b LEFT JOIN generators g ON g.id=b.generator_id WHERE g.id IS NULL"
        ).fetchone()[0],
        "orphan_hyperedges": connection.execute(
            "SELECT COUNT(*) FROM hyperedges e LEFT JOIN generators l ON l.id=e.left_id LEFT JOIN generators r ON r.id=e.right_id WHERE l.id IS NULL OR r.id IS NULL"
        ).fetchone()[0],
        "missing_negative_controls": connection.execute(
            "SELECT COUNT(*) FROM generators g LEFT JOIN negative_controls n ON n.generator_id=g.id WHERE n.id IS NULL"
        ).fetchone()[0],
        "missing_validations": connection.execute(
            "SELECT COUNT(*) FROM generators g LEFT JOIN validations v ON v.generator_id=g.id WHERE v.id IS NULL"
        ).fetchone()[0],
        "high_risk_not_exhaustive": connection.execute(
            "SELECT COUNT(*) FROM validations WHERE risk_tier='high' AND validation_mode!='exhaustive_required'"
        ).fetchone()[0],
    }


def audit_ultra_catalog(root: Path = DEFAULT_ROOT) -> UltraAuditReport:
    manifest = load_manifest(root)
    expected_raw = manifest["counts"]
    assert isinstance(expected_raw, dict)
    expected = {
        "generators": int(expected_raw["generators"]),
        "benchmarks": int(expected_raw["benchmarks"]),
        "hyperedges": int(expected_raw["hyperedges"]),
        "negative_controls": int(expected_raw["negative_controls"]),
        "validations": int(expected_raw["validations"]),
    }
    totals = {key: 0 for key in (
        "generators", "benchmarks", "hyperedges", "negative_controls", "validations",
        "orphan_benchmarks", "orphan_hyperedges", "missing_negative_controls",
        "missing_validations", "high_risk_not_exhaustive",
    )}
    for path in _partition_paths(root):
        connection = _connect(path)
        try:
            local = _audit_connection(connection)
        finally:
            connection.close()
        for key, value in local.items():
            totals[key] += value

    routing = _connect(_routing_database(root))
    try:
        routing_count = routing.execute("SELECT COUNT(*) FROM generators").fetchone()[0]
        duplicate_coordinate_groups = routing.execute(
            "SELECT COUNT(*) FROM (SELECT domain,family,scale,representation,regime,COUNT(*) c FROM generators GROUP BY domain,family,scale,representation,regime HAVING c>1)"
        ).fetchone()[0]
    finally:
        routing.close()

    counts = {key: totals[key] for key in expected}
    valid = (
        counts == expected
        and routing_count == expected["generators"]
        and totals["orphan_benchmarks"] == 0
        and totals["orphan_hyperedges"] == 0
        and totals["missing_negative_controls"] == 0
        and totals["missing_validations"] == 0
        and totals["high_risk_not_exhaustive"] == 0
        and duplicate_coordinate_groups == 0
    )
    return UltraAuditReport(
        valid=valid,
        counts=counts,
        expected=expected,
        orphan_benchmarks=totals["orphan_benchmarks"],
        orphan_hyperedges=totals["orphan_hyperedges"],
        missing_negative_controls=totals["missing_negative_controls"],
        missing_validations=totals["missing_validations"],
        high_risk_not_exhaustive=totals["high_risk_not_exhaustive"],
        duplicate_coordinate_groups=duplicate_coordinate_groups,
        combined_fingerprint=str(manifest["combined_fingerprint"]),
    )


def iter_jsonl_records(directory: Path) -> Iterator[dict[str, object]]:
    for path in sorted(directory.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)
