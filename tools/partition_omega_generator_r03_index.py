#!/usr/bin/env python3
"""Partition the R0.3 Ultra SQLite index by domain.

The generated monolithic index is useful for local validation but can exceed
GitHub's 100 MB per-file limit. This tool creates one domain database per domain
plus a compact routing database, verifies aggregate counts, updates the manifest,
and removes the monolithic database.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

DOMAIN_SCHEMA = """
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
CREATE TABLE generators (
    id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE, domain TEXT, family TEXT,
    scale TEXT, representation TEXT, regime TEXT, status TEXT,
    invariant_name TEXT, risk TEXT, risk_tier TEXT,
    supports_inverse INTEGER, payload TEXT
);
CREATE TABLE benchmarks (
    id TEXT PRIMARY KEY, generator_id TEXT, variant TEXT, payload TEXT
);
CREATE TABLE hyperedges (
    id TEXT PRIMARY KEY, left_id TEXT, right_id TEXT, payload TEXT
);
CREATE TABLE negative_controls (
    id TEXT PRIMARY KEY, generator_id TEXT UNIQUE, payload TEXT
);
CREATE TABLE validations (
    id TEXT PRIMARY KEY, generator_id TEXT UNIQUE, validation_mode TEXT,
    risk_tier TEXT, payload TEXT
);
CREATE INDEX idx_generators_coordinates
    ON generators(domain, family, scale, representation, regime);
CREATE INDEX idx_generators_risk ON generators(risk_tier, risk);
CREATE INDEX idx_benchmarks_generator ON benchmarks(generator_id);
CREATE INDEX idx_edges_left ON hyperedges(left_id);
CREATE INDEX idx_edges_right ON hyperedges(right_id);
"""

ROUTING_SCHEMA = """
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
CREATE TABLE generators (
    id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE, domain TEXT, family TEXT,
    scale TEXT, representation TEXT, regime TEXT, status TEXT,
    invariant_name TEXT, risk TEXT, risk_tier TEXT, supports_inverse INTEGER
);
CREATE INDEX idx_routing_coordinates
    ON generators(domain, family, scale, representation, regime);
CREATE INDEX idx_routing_risk ON generators(risk_tier, risk);
"""


def _safe_name(domain: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in domain)


def partition_index(root: Path) -> dict[str, object]:
    output = root / "generated" / "omega_generator_discovery_r03_ultra"
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = output / "index" / "omega_generator_r03_ultra.sqlite3"
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    domains = list(manifest["axes"]["domains"])
    partition_dir = output / "index" / "domains"
    partition_dir.mkdir(parents=True, exist_ok=True)
    for stale in partition_dir.glob("*.sqlite3"):
        stale.unlink()
    routing_path = output / "index" / "routing.sqlite3"
    if routing_path.exists():
        routing_path.unlink()

    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    routing = sqlite3.connect(routing_path)
    routing.executescript(ROUTING_SCHEMA)
    partition_paths: list[Path] = []
    per_domain: dict[str, dict[str, int]] = {}
    try:
        routing.executemany(
            "INSERT INTO generators VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                (
                    row["id"], row["ordinal"], row["domain"], row["family"],
                    row["scale"], row["representation"], row["regime"],
                    row["status"], row["invariant_name"], row["risk"],
                    row["risk_tier"], row["supports_inverse"],
                )
                for row in source.execute("SELECT * FROM generators ORDER BY ordinal")
            ),
        )
        routing.commit()
        routing.execute("VACUUM")

        for domain in domains:
            path = partition_dir / f"{_safe_name(domain)}.sqlite3"
            partition_paths.append(path)
            target = sqlite3.connect(path)
            target.executescript(DOMAIN_SCHEMA)
            try:
                target.executemany(
                    "INSERT INTO generators VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        tuple(row)
                        for row in source.execute(
                            "SELECT * FROM generators WHERE domain=? ORDER BY ordinal", (domain,)
                        )
                    ),
                )
                target.executemany(
                    "INSERT INTO benchmarks VALUES (?,?,?,?)",
                    (
                        tuple(row)
                        for row in source.execute(
                            "SELECT b.* FROM benchmarks b JOIN generators g ON g.id=b.generator_id WHERE g.domain=? ORDER BY b.id",
                            (domain,),
                        )
                    ),
                )
                target.executemany(
                    "INSERT INTO hyperedges VALUES (?,?,?,?)",
                    (
                        tuple(row)
                        for row in source.execute(
                            "SELECT e.* FROM hyperedges e JOIN generators g ON g.id=e.left_id WHERE g.domain=? ORDER BY e.id",
                            (domain,),
                        )
                    ),
                )
                target.executemany(
                    "INSERT INTO negative_controls VALUES (?,?,?)",
                    (
                        tuple(row)
                        for row in source.execute(
                            "SELECT n.* FROM negative_controls n JOIN generators g ON g.id=n.generator_id WHERE g.domain=? ORDER BY n.id",
                            (domain,),
                        )
                    ),
                )
                target.executemany(
                    "INSERT INTO validations VALUES (?,?,?,?,?)",
                    (
                        tuple(row)
                        for row in source.execute(
                            "SELECT v.* FROM validations v JOIN generators g ON g.id=v.generator_id WHERE g.domain=? ORDER BY v.id",
                            (domain,),
                        )
                    ),
                )
                target.commit()
                target.execute("VACUUM")
                per_domain[domain] = {
                    table: target.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("generators", "benchmarks", "hyperedges", "negative_controls", "validations")
                }
            finally:
                target.close()
    finally:
        routing.close()
        source.close()

    aggregate = {
        table: sum(counts[table] for counts in per_domain.values())
        for table in ("generators", "benchmarks", "hyperedges", "negative_controls", "validations")
    }
    expected = {
        "generators": int(manifest["counts"]["generators"]),
        "benchmarks": int(manifest["counts"]["benchmarks"]),
        "hyperedges": int(manifest["counts"]["hyperedges"]),
        "negative_controls": int(manifest["counts"]["negative_controls"]),
        "validations": int(manifest["counts"]["validations"]),
    }
    routing_connection = sqlite3.connect(routing_path)
    try:
        routing_count = routing_connection.execute("SELECT COUNT(*) FROM generators").fetchone()[0]
    finally:
        routing_connection.close()
    if aggregate != expected or routing_count != expected["generators"]:
        raise ValueError({"aggregate": aggregate, "expected": expected, "routing_count": routing_count})

    sizes = {str(path.relative_to(output)): path.stat().st_size for path in [routing_path, *partition_paths]}
    too_large = {path: size for path, size in sizes.items() if size >= 100_000_000}
    if too_large:
        raise ValueError({"files_over_github_limit": too_large})

    source_path.unlink()
    manifest["database"] = {
        "mode": "partitioned_by_domain",
        "routing": str(routing_path.relative_to(output)),
        "partitions": [str(path.relative_to(output)) for path in partition_paths],
        "counts": aggregate,
        "maximum_partition_bytes": max(sizes.values()),
    }
    manifest["audit"]["partitioned_database_valid"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "valid": True,
        "routing_count": routing_count,
        "aggregate": aggregate,
        "partitions": len(partition_paths),
        "maximum_partition_bytes": max(sizes.values()),
        "source_removed": not source_path.exists(),
        "per_domain": per_domain,
    }
    (output / "index" / "partition-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = partition_index(Path(args.root).resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
