#!/usr/bin/env python3
"""Audit Tristan Web OS provenance without mistaking provenance for proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "apps" / "tristan-8fire-site" / "data"
MANIFEST_PATH = DATA / "provenance.json"
INDEX_PATH = ROOT / "content" / "generated" / "PROVENANCE_INDEX.md"
HEX64 = re.compile(r"^[a-f0-9]{64}$")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit() -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def add(bucket: list[dict[str, str]], code: str, message: str, object_id: str = "") -> None:
        bucket.append({"code": code, "message": message, "object_id": object_id})

    theories = load(DATA / "theories.json")["theories"]
    claims = load(DATA / "claims.json")["claims"]
    manifest = load(MANIFEST_PATH)
    theory_ids = {item["id"] for item in theories}
    claim_ids = {item["id"] for item in claims}

    if manifest.get("schema_version") != "0.3.0":
        add(errors, "manifest.version", "schema_version must be 0.3.0")
    if manifest.get("hash_algorithm") != "sha256":
        add(errors, "manifest.hash_algorithm", "hash_algorithm must be sha256")

    sources = manifest.get("sources", [])
    source_ids = [item.get("id", "") for item in sources]
    duplicate_sources = [value for value, count in Counter(source_ids).items() if count > 1]
    for source_id in duplicate_sources:
        add(errors, "source.duplicate", "Duplicate source id", source_id)

    status_counts = Counter()
    for source in sources:
        source_id = str(source.get("id", ""))
        relative = str(source.get("path", ""))
        status = str(source.get("status", ""))
        status_counts[status] += 1
        if not relative:
            add(errors, "source.path", "Source path is empty", source_id)
            continue
        resolved = (ROOT / relative).resolve()
        if resolved != ROOT and ROOT not in resolved.parents:
            if status != "blocked-outside-repository":
                add(errors, "source.escape", "Path escapes repository but is not blocked", source_id)
            continue
        if status == "resolved-file":
            if not resolved.is_file():
                add(errors, "source.file_missing", f"Resolved file no longer exists: {relative}", source_id)
            else:
                expected = source.get("sha256")
                if not isinstance(expected, str) or not HEX64.fullmatch(expected):
                    add(errors, "source.hash_format", "Resolved file requires a 64-character SHA-256", source_id)
                elif sha256(resolved) != expected:
                    add(errors, "source.hash_mismatch", f"SHA-256 mismatch for {relative}", source_id)
                if source.get("size_bytes") != resolved.stat().st_size:
                    add(errors, "source.size_mismatch", f"Size mismatch for {relative}", source_id)
        elif status == "resolved-directory":
            if not resolved.is_dir():
                add(errors, "source.directory_missing", f"Resolved directory no longer exists: {relative}", source_id)
            if source.get("sha256") is not None:
                add(errors, "source.directory_hash", "Directories must not claim a file SHA-256", source_id)
        elif status == "unresolved":
            if resolved.exists():
                add(errors, "source.stale_unresolved", f"Reference now exists and provenance must be regenerated: {relative}", source_id)
            add(warnings, "source.unresolved", f"Unresolved public source reference: {relative}", source_id)
        elif status != "blocked-outside-repository":
            add(errors, "source.status", f"Unknown source status {status}", source_id)

        for theory_id in source.get("theory_ids", []):
            if theory_id not in theory_ids:
                add(errors, "source.theory_orphan", f"Unknown theory {theory_id}", source_id)
        for claim_id in source.get("claim_ids", []):
            if claim_id not in claim_ids:
                add(errors, "source.claim_orphan", f"Unknown claim {claim_id}", source_id)

    theory_rows = manifest.get("theory_provenance", [])
    claim_rows = manifest.get("claim_provenance", [])
    if len(theory_rows) != len(theories):
        add(errors, "coverage.theories", f"Expected {len(theories)} theory rows, got {len(theory_rows)}")
    if len(claim_rows) != len(claims):
        add(errors, "coverage.claims", f"Expected {len(claims)} claim rows, got {len(claim_rows)}")
    if {item.get("theory_id") for item in theory_rows} != theory_ids:
        add(errors, "coverage.theory_ids", "Theory provenance does not cover the exact public theory set")
    if {item.get("claim_id") for item in claim_rows} != claim_ids:
        add(errors, "coverage.claim_ids", "Claim provenance does not cover the exact public claim set")
    for row in claim_rows:
        if row.get("automatic_promotion") is not False:
            add(errors, "claim.auto_promotion", "Provenance may not authorize automatic promotion", str(row.get("claim_id", "")))

    metrics = manifest.get("metrics", {})
    expected_metrics = {
        "sources": len(sources),
        "resolved_files": status_counts["resolved-file"],
        "resolved_directories": status_counts["resolved-directory"],
        "unresolved": status_counts["unresolved"],
        "blocked_outside_repository": status_counts["blocked-outside-repository"],
        "theories": len(theories),
        "claims": len(claims),
    }
    for key, expected in expected_metrics.items():
        if metrics.get(key) != expected:
            add(errors, "metrics.mismatch", f"{key}: expected {expected}, got {metrics.get(key)}")
    if not INDEX_PATH.is_file():
        add(errors, "index.missing", "Generated provenance index is missing")

    return {
        "audit": "tristan-web-os-provenance",
        "status": "fail" if errors else "pass-with-debt" if warnings else "pass",
        "metrics": expected_metrics,
        "errors": errors,
        "warnings": warnings,
        "epistemic_boundary": (
            "Resolved paths and matching hashes establish repository identity only. "
            "Unresolved references remain visible debt; neither state certifies scientific validity."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict-unresolved", action="store_true")
    args = parser.parse_args(argv)
    report = audit()
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if report["errors"]:
        return 1
    if args.strict_unresolved and report["warnings"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
