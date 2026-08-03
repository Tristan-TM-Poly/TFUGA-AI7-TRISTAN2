"""Strict audit for Ω-PROBLEM-ATLAS-T∞ R0.4 source bundles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from omega_millennium_t.r03.atlas import stable_digest

from .source_adapters import _file_receipt, _read_jsonl


def _snapshot_digest(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "snapshot_digest"}
    return stable_digest(payload)


def _receipt_digest(row: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in row.items()
        if key not in {"receipt_id", "receipt_digest"}
    }
    return stable_digest(payload)


def audit_source_bundle_strict(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "source_snapshots.jsonl",
        "imports.jsonl",
        "status_receipts.jsonl",
        "quarantine.jsonl",
        "manifest.json",
        "report.json",
    }
    missing = sorted(name for name in required if not (output / name).exists())
    if missing:
        return {
            "schema": "omega-problem-source-adapter-audit/4",
            "valid": False,
            "errors": [f"missing artifact: {name}" for name in missing],
            "solution_claimed": False,
            "current_status_certification_claimed": False,
        }

    errors: list[str] = []
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))

    manifest_payload = {key: value for key, value in manifest.items() if key != "digest"}
    if manifest.get("digest") != stable_digest(manifest_payload):
        errors.append("manifest digest mismatch")
    report_payload = {key: value for key, value in report.items() if key != "digest"}
    if report.get("digest") != stable_digest(report_payload):
        errors.append("report digest mismatch")
    if report.get("manifest_digest") != manifest.get("digest"):
        errors.append("report manifest_digest mismatch")

    artifact_receipts = {item.get("path"): item for item in manifest.get("artifacts", [])}
    artifact_names = (
        "source_snapshots.jsonl",
        "imports.jsonl",
        "status_receipts.jsonl",
        "quarantine.jsonl",
    )
    for name in artifact_names:
        expected = artifact_receipts.get(name)
        if expected is None:
            errors.append(f"manifest missing {name}")
            continue
        actual = _file_receipt(output / name)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected.get(field):
                errors.append(f"{name}: {field} mismatch")

    snapshots = _read_jsonl(output / "source_snapshots.jsonl")
    imports = _read_jsonl(output / "imports.jsonl")
    receipts = _read_jsonl(output / "status_receipts.jsonl")
    quarantined = _read_jsonl(output / "quarantine.jsonl")

    snapshot_ids: set[str] = set()
    snapshot_digests: dict[str, str] = {}
    source_ids: set[str] = set()
    for snapshot in snapshots:
        snapshot_id = str(snapshot.get("snapshot_id", ""))
        if not snapshot_id:
            errors.append("snapshot with blank snapshot_id")
            continue
        if snapshot_id in snapshot_ids:
            errors.append(f"duplicate snapshot_id: {snapshot_id}")
        snapshot_ids.add(snapshot_id)
        source_ids.add(str(snapshot.get("source_id", "")))
        expected_digest = _snapshot_digest(snapshot)
        if snapshot.get("snapshot_digest") != expected_digest:
            errors.append(f"{snapshot_id}: snapshot digest mismatch")
        snapshot_digests[snapshot_id] = expected_digest

    receipt_ids: set[str] = set()
    receipts_by_id: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        receipt_id = str(receipt.get("receipt_id", ""))
        if not receipt_id:
            errors.append("receipt with blank receipt_id")
            continue
        if receipt_id in receipt_ids:
            errors.append(f"duplicate receipt_id: {receipt_id}")
        receipt_ids.add(receipt_id)
        receipts_by_id[receipt_id] = receipt
        if receipt.get("receipt_digest") != _receipt_digest(receipt):
            errors.append(f"{receipt_id}: receipt digest mismatch")
        snapshot_id = str(receipt.get("source_snapshot_id", ""))
        if snapshot_id not in snapshot_ids:
            errors.append(f"{receipt_id}: unknown source snapshot")
        elif receipt.get("source_snapshot_digest") != snapshot_digests.get(snapshot_id):
            errors.append(f"{receipt_id}: source snapshot digest mismatch")
        blockers = receipt.get("blockers")
        if not isinstance(blockers, list):
            errors.append(f"{receipt_id}: blockers must be a list")
        if receipt.get("claim_allowed") is True and blockers:
            errors.append(f"{receipt_id}: allowed claim has blockers")

    import_ids: set[tuple[str, str, str]] = set()
    current_open_claim_count = 0
    for row in imports:
        identity = (
            str(row.get("problem_id", "")),
            str(row.get("source_id", "")),
            str(row.get("source_snapshot_id", "")),
        )
        if identity in import_ids:
            errors.append(f"duplicate import identity: {identity}")
        import_ids.add(identity)
        if row.get("solution_claimed") is not False:
            errors.append(f"{row.get('problem_id')}: solution claim present")
        snapshot_id = str(row.get("source_snapshot_id", ""))
        if snapshot_id not in snapshot_ids:
            errors.append(f"{row.get('problem_id')}: missing source snapshot")
        elif row.get("source_snapshot_digest") != snapshot_digests.get(snapshot_id):
            errors.append(f"{row.get('problem_id')}: source snapshot digest mismatch")
        receipt_id = str(row.get("status_receipt_id", ""))
        receipt = receipts_by_id.get(receipt_id)
        if receipt is None:
            errors.append(f"{row.get('problem_id')}: missing status receipt")
        elif receipt.get("problem_id") != row.get("problem_id"):
            errors.append(f"{row.get('problem_id')}: receipt problem mismatch")
        if row.get("current_open_status_claimed"):
            current_open_claim_count += 1
            if not row.get("source_verified_at"):
                errors.append(f"{row.get('problem_id')}: open claim lacks verification date")
            if receipt is None or receipt.get("claim_allowed") is not True:
                errors.append(f"{row.get('problem_id')}: open claim receipt not allowed")

    quarantine_ids: set[str] = set()
    for row in quarantined:
        quarantine_id = str(row.get("quarantine_id", ""))
        if not quarantine_id:
            errors.append("quarantine record with blank quarantine_id")
            continue
        if quarantine_id in quarantine_ids:
            errors.append(f"duplicate quarantine_id: {quarantine_id}")
        quarantine_ids.add(quarantine_id)
        if str(row.get("snapshot_id", "")) not in snapshot_ids:
            errors.append(f"{quarantine_id}: unknown snapshot")
        reason_codes = row.get("reason_codes")
        if not isinstance(reason_codes, list) or not reason_codes:
            errors.append(f"{quarantine_id}: missing reason codes")
        raw_record = row.get("raw_record")
        if not isinstance(raw_record, dict):
            errors.append(f"{quarantine_id}: raw_record must be object")
        elif row.get("raw_record_digest") != stable_digest(raw_record):
            errors.append(f"{quarantine_id}: raw record digest mismatch")

    expected_counts = {
        "snapshot_count": len(snapshots),
        "source_count": len(source_ids),
        "input_record_count": len(receipts),
        "accepted_import_count": len(imports),
        "status_receipt_count": len(receipts),
        "quarantine_count": len(quarantined),
        "current_open_claim_count": current_open_claim_count,
        "solution_claim_count": 0,
    }
    for field, actual in expected_counts.items():
        if report.get(field) != actual:
            errors.append(f"report {field}: expected {actual}, got {report.get(field)}")
    if len(imports) + len(quarantined) != len(receipts):
        errors.append("accepted plus quarantined records must equal receipt count")

    for forbidden in (
        "source_retrieval_certified",
        "current_status_certification_claimed",
        "scientific_validation_claimed",
        "solution_claimed",
        "formal_proof_claimed",
    ):
        if report.get(forbidden) is not False:
            errors.append(f"{forbidden} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")

    return {
        "schema": "omega-problem-source-adapter-audit/4",
        "valid": not errors,
        "errors": errors,
        "snapshot_count": len(snapshots),
        "source_count": len(source_ids),
        "import_count": len(imports),
        "receipt_count": len(receipts),
        "quarantine_count": len(quarantined),
        "current_open_claim_count": current_open_claim_count,
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
        "current_status_certification_claimed": False,
    }
