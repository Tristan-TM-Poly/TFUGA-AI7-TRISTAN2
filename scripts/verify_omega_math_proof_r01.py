#!/usr/bin/env python3
"""Verify Ω-MATH-PROOF R0.1 discovery and OAK boundaries."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "omega_math_proof_r01" / "decoded"
OUT = ROOT / "artifacts" / "omega_math_proof_r01" / "verification_report.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    required = [
        BASE / "catalog" / "books.jsonl",
        BASE / "metadata" / "work_unit.json",
        BASE / "metadata" / "evidence_receipt.json",
        BASE / "metadata" / "source_anchors.jsonl",
        BASE / "metadata" / "oak_report.json",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    checks: list[dict] = []
    checks.append({"name": "required_files", "status": "PASS" if not missing else "FAIL", "missing": missing})

    records = []
    catalog = BASE / "catalog" / "books.jsonl"
    if catalog.exists():
        records = [json.loads(line) for line in catalog.read_text(encoding="utf-8").splitlines() if line.strip()]
    checks.append({"name": "catalog_exactly_64", "status": "PASS" if len(records) == 64 else "FAIL", "value": len(records)})

    ids = [record.get("catalog_id") for record in records]
    checks.append({"name": "catalog_ids_unique", "status": "PASS" if len(ids) == len(set(ids)) == 64 else "FAIL"})
    checks.append({
        "name": "source_urls_present",
        "status": "PASS" if records and all(record.get("discovery_url") or record.get("direct_pdf_url") for record in records) else "FAIL",
    })
    checks.append({
        "name": "pdf_availability_discovery_claim",
        "status": "PASS" if records and all(record.get("pdf_availability_verified") is True for record in records) else "FAIL",
    })

    receipt_path = BASE / "metadata" / "evidence_receipt.json"
    receipt = load_json(receipt_path) if receipt_path.exists() else {}
    checks.append({
        "name": "binary_fetch_not_falsely_claimed",
        "status": "PASS" if receipt.get("document_count") == 0 else "FAIL",
        "document_count": receipt.get("document_count"),
    })

    oak_path = BASE / "metadata" / "oak_report.json"
    oak = load_json(oak_path) if oak_path.exists() else {}
    checks.append({
        "name": "oak_discovery_fetch_boundary",
        "status": "PASS" if oak.get("verdict") == "HOLD" else "FAIL",
        "verdict": oak.get("verdict"),
    })

    pdfs = list(BASE.rglob("*.pdf"))
    checks.append({
        "name": "no_third_party_pdf_bytes_committed",
        "status": "PASS" if not pdfs else "FAIL",
        "pdf_count": len(pdfs),
    })

    failures = [c for c in checks if c["status"] != "PASS"]
    report = {
        "schema_version": "1.0",
        "component": "omega-math-proof-research-os-r0.1",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "claim_boundary": (
            "R0.1 certifies discovery-contract integrity only. It does not certify the mathematical "
            "truth of source content, successful download of 64 books, redistribution rights, or semantic "
            "equivalence of future formalizations."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
