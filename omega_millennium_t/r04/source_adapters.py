"""Ω-PROBLEM-ATLAS-T∞ R0.4 source adapters.

This module compiles revision-pinned, offline source snapshots into the R0.3
JSONL import contract.  It is deliberately fail-closed:

* a current-open-status claim requires a dated verification receipt;
* malformed or ambiguous records are quarantined rather than guessed;
* source retrieval, parsing, and status verification remain separate events;
* no record may claim a solution;
* fixtures and tests run without network access.

The adapters do not certify the current state of any external catalog.  They
certify only that a supplied snapshot satisfied this software contract.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from omega_millennium_t.r03.atlas import FRONTS, canonicalize_title, stable_digest


SNAPSHOT_SCHEMA = "omega-problem-source-snapshot/4"
REPORT_SCHEMA = "omega-problem-source-adapter-report/4"
MANIFEST_SCHEMA = "omega-problem-source-adapter-manifest/4"

ALLOWED_OBSERVED_STATUSES = {
    "open",
    "solved",
    "disproved",
    "independent",
    "unknown",
    "requires_refresh",
}

ALLOWED_VERIFICATION_BASES = {
    "primary_source",
    "curated_source_plus_primary_refs",
    "fixture_only",
    "unverified",
}

SOURCE_POLICIES: Mapping[str, Mapping[str, Any]] = {
    "clay": {
        "requires_revision": False,
        "allows_open_claim": True,
        "accepted_basis": {"primary_source"},
    },
    "erdos_problems": {
        "requires_revision": False,
        "allows_open_claim": True,
        "accepted_basis": {"curated_source_plus_primary_refs", "primary_source"},
    },
    "formal_conjectures": {
        "requires_revision": True,
        "allows_open_claim": True,
        "accepted_basis": {"curated_source_plus_primary_refs", "primary_source"},
    },
    "open_quantum_problems": {
        "requires_revision": False,
        "allows_open_claim": True,
        "accepted_basis": {"curated_source_plus_primary_refs", "primary_source"},
    },
    "aim_problem_lists": {
        "requires_revision": False,
        "allows_open_claim": True,
        "accepted_basis": {"curated_source_plus_primary_refs", "primary_source"},
    },
    "competition_archive": {
        "requires_revision": True,
        "allows_open_claim": False,
        "accepted_basis": set(),
    },
    "test_fixture": {
        "requires_revision": False,
        "allows_open_claim": False,
        "accepted_basis": set(),
    },
}


@dataclass(frozen=True)
class SourceSnapshot:
    snapshot_id: str
    source_id: str
    source_url: str
    retrieved_at: str
    revision: str | None
    retrieval_mode: str
    license_note: str
    records: tuple[Mapping[str, Any], ...]
    snapshot_digest: str


@dataclass(frozen=True)
class StatusReceipt:
    receipt_id: str
    problem_id: str
    source_id: str
    source_locator: str
    observed_status: str
    status_verified_at: str | None
    verification_basis: str
    source_revision: str | None
    source_snapshot_id: str
    source_snapshot_digest: str
    current_open_status_claimed: bool
    claim_allowed: bool
    blockers: tuple[str, ...]
    receipt_digest: str


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    source_id: str
    snapshot_id: str
    record_index: int
    reason_codes: tuple[str, ...]
    raw_record_digest: str
    raw_record: Mapping[str, Any]


def _parse_iso8601(value: str, *, field_name: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError(f"{field_name} is blank")
    normalized = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} requires timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    normalized = canonicalize_title(value).replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_\-]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "record"


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "sha256": _sha256_bytes(data),
        "bytes": len(data),
        "rows": sum(1 for line in data.splitlines() if line.strip()),
    }


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def load_source_snapshot(path_like: str | Path) -> SourceSnapshot:
    path = Path(path_like)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError(f"{path}: unsupported snapshot schema")

    source_id = str(payload.get("source_id", "")).strip()
    if source_id not in SOURCE_POLICIES:
        raise ValueError(f"{path}: unsupported source_id {source_id!r}")
    policy = SOURCE_POLICIES[source_id]

    source_url = str(payload.get("source_url", "")).strip()
    if not source_url.startswith("https://"):
        raise ValueError(f"{path}: source_url must use https")

    retrieved_at = _parse_iso8601(str(payload.get("retrieved_at", "")), field_name="retrieved_at")
    revision_value = payload.get("revision")
    revision = str(revision_value).strip() if revision_value is not None else None
    if policy["requires_revision"] and not revision:
        raise ValueError(f"{path}: source {source_id} requires revision")

    records_raw = payload.get("records")
    if not isinstance(records_raw, list):
        raise ValueError(f"{path}: records must be a list")
    records: tuple[Mapping[str, Any], ...] = tuple(
        item for item in records_raw if isinstance(item, Mapping)
    )
    if len(records) != len(records_raw):
        raise ValueError(f"{path}: every record must be an object")

    base = {
        "schema": SNAPSHOT_SCHEMA,
        "snapshot_id": str(payload.get("snapshot_id", "")).strip(),
        "source_id": source_id,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "revision": revision,
        "retrieval_mode": str(payload.get("retrieval_mode", "offline_fixture")).strip(),
        "license_note": str(payload.get("license_note", "")).strip(),
        "records": [dict(item) for item in records],
    }
    if not base["snapshot_id"]:
        raise ValueError(f"{path}: snapshot_id is blank")
    if not base["license_note"]:
        raise ValueError(f"{path}: license_note is blank")

    return SourceSnapshot(
        snapshot_id=base["snapshot_id"],
        source_id=source_id,
        source_url=source_url,
        retrieved_at=retrieved_at,
        revision=revision,
        retrieval_mode=base["retrieval_mode"],
        license_note=base["license_note"],
        records=records,
        snapshot_digest=stable_digest(base),
    )


def _validate_record(
    snapshot: SourceSnapshot,
    item: Mapping[str, Any],
    index: int,
) -> tuple[dict[str, Any] | None, StatusReceipt, QuarantineRecord | None]:
    errors: list[str] = []
    title = str(item.get("title", "")).strip()
    problem_id = str(item.get("problem_id") or _slug(title)).strip()
    front = str(item.get("front", "")).strip()
    observed_status = str(item.get("observed_status", "requires_refresh")).strip()
    source_locator = str(item.get("source_locator", "")).strip()
    statement = item.get("statement")
    statement_text = str(statement).strip() if statement is not None else None
    verification_basis = str(item.get("verification_basis", "unverified")).strip()
    status_verified_raw = item.get("status_verified_at")
    current_open_claim = bool(item.get("current_open_status_claimed", False))
    solution_claim = bool(item.get("solution_claimed", False))

    if not title:
        errors.append("blank_title")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", problem_id):
        errors.append("invalid_problem_id")
    if front not in FRONTS:
        errors.append("unknown_front")
    if observed_status not in ALLOWED_OBSERVED_STATUSES:
        errors.append("unknown_observed_status")
    if not source_locator:
        errors.append("missing_source_locator")
    if verification_basis not in ALLOWED_VERIFICATION_BASES:
        errors.append("unknown_verification_basis")
    if solution_claim:
        errors.append("solution_claim_forbidden")

    status_verified_at: str | None = None
    if status_verified_raw is not None:
        try:
            status_verified_at = _parse_iso8601(
                str(status_verified_raw), field_name="status_verified_at"
            )
        except ValueError:
            errors.append("invalid_status_verified_at")

    policy = SOURCE_POLICIES[snapshot.source_id]
    claim_blockers: list[str] = []
    if current_open_claim:
        if observed_status != "open":
            claim_blockers.append("open_claim_status_mismatch")
        if not status_verified_at:
            claim_blockers.append("open_claim_missing_dated_receipt")
        if not policy["allows_open_claim"]:
            claim_blockers.append("source_policy_forbids_open_claim")
        if verification_basis not in policy["accepted_basis"]:
            claim_blockers.append("verification_basis_not_accepted")
        if snapshot.retrieval_mode == "offline_fixture" and snapshot.source_id != "test_fixture":
            claim_blockers.append("offline_fixture_cannot_certify_current_status")

    claim_allowed = current_open_claim and not claim_blockers
    if current_open_claim and claim_blockers:
        errors.extend(claim_blockers)

    receipt_base = {
        "problem_id": problem_id,
        "source_id": snapshot.source_id,
        "source_locator": source_locator,
        "observed_status": observed_status,
        "status_verified_at": status_verified_at,
        "verification_basis": verification_basis,
        "source_revision": snapshot.revision,
        "source_snapshot_id": snapshot.snapshot_id,
        "source_snapshot_digest": snapshot.snapshot_digest,
        "current_open_status_claimed": current_open_claim,
        "claim_allowed": claim_allowed,
        "blockers": sorted(set(claim_blockers)),
    }
    receipt_id = f"receipt::{snapshot.snapshot_id}::{index:05d}::{problem_id}"
    receipt = StatusReceipt(
        receipt_id=receipt_id,
        problem_id=problem_id,
        source_id=snapshot.source_id,
        source_locator=source_locator,
        observed_status=observed_status,
        status_verified_at=status_verified_at,
        verification_basis=verification_basis,
        source_revision=snapshot.revision,
        source_snapshot_id=snapshot.snapshot_id,
        source_snapshot_digest=snapshot.snapshot_digest,
        current_open_status_claimed=current_open_claim,
        claim_allowed=claim_allowed,
        blockers=tuple(sorted(set(claim_blockers))),
        receipt_digest=stable_digest(receipt_base),
    )

    if errors:
        raw_digest = stable_digest(dict(item))
        quarantine = QuarantineRecord(
            quarantine_id=f"quarantine::{snapshot.snapshot_id}::{index:05d}::{raw_digest[:12]}",
            source_id=snapshot.source_id,
            snapshot_id=snapshot.snapshot_id,
            record_index=index,
            reason_codes=tuple(sorted(set(errors))),
            raw_record_digest=raw_digest,
            raw_record=dict(item),
        )
        return None, receipt, quarantine

    import_status = observed_status
    if observed_status == "open" and not claim_allowed:
        import_status = "open_status_requires_refresh"
    elif observed_status == "solved":
        import_status = "solved_benchmark"
    elif observed_status in {"disproved", "independent"}:
        import_status = f"{observed_status}_status_observed"
    elif observed_status in {"unknown", "requires_refresh"}:
        import_status = "status_requires_refresh"

    import_row = {
        "problem_id": problem_id,
        "title": title,
        "front": front,
        "status": import_status,
        "source_id": snapshot.source_id,
        "source_locator": source_locator,
        "source_verified_at": status_verified_at if claim_allowed else None,
        "statement": statement_text,
        "current_open_status_claimed": claim_allowed,
        "solution_claimed": False,
        "source_snapshot_id": snapshot.snapshot_id,
        "source_revision": snapshot.revision,
        "source_snapshot_digest": snapshot.snapshot_digest,
        "status_receipt_id": receipt_id,
        "adapter_provenance_digest": stable_digest(
            {
                "snapshot": snapshot.snapshot_digest,
                "record_index": index,
                "record": dict(item),
            }
        ),
    }
    return import_row, receipt, None


def compile_source_bundle(
    snapshot_paths: Sequence[str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    snapshots = tuple(sorted(
        (load_source_snapshot(path) for path in snapshot_paths),
        key=lambda item: (item.source_id, item.snapshot_id),
    ))
    snapshot_ids = [snapshot.snapshot_id for snapshot in snapshots]
    if len(snapshot_ids) != len(set(snapshot_ids)):
        raise ValueError("duplicate snapshot_id")

    imports: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for snapshot in snapshots:
        for index, item in enumerate(snapshot.records, start=1):
            import_row, receipt, quarantine = _validate_record(snapshot, item, index)
            receipts.append(asdict(receipt))
            if import_row is not None:
                imports.append(import_row)
            if quarantine is not None:
                quarantined.append(asdict(quarantine))

    imports.sort(key=lambda row: (row["front"], row["problem_id"], row["source_id"]))
    receipts.sort(key=lambda row: row["receipt_id"])
    quarantined.sort(key=lambda row: row["quarantine_id"])
    snapshot_rows = [asdict(snapshot) for snapshot in snapshots]

    _write_jsonl(output / "source_snapshots.jsonl", snapshot_rows)
    _write_jsonl(output / "imports.jsonl", imports)
    _write_jsonl(output / "status_receipts.jsonl", receipts)
    _write_jsonl(output / "quarantine.jsonl", quarantined)

    artifact_names = (
        "source_snapshots.jsonl",
        "imports.jsonl",
        "status_receipts.jsonl",
        "quarantine.jsonl",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifacts": [_file_receipt(output / name) for name in artifact_names],
        "snapshot_ids": snapshot_ids,
        "permanent_total_cap": None,
        "solution_claimed": False,
        "current_status_certification_claimed": False,
    }
    manifest["digest"] = stable_digest({k: v for k, v in manifest.items() if k != "digest"})
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": REPORT_SCHEMA,
        "status": "CERTIFIED_OFFLINE_SOURCE_ADAPTER_FIXTURE_R0_4",
        "snapshot_count": len(snapshots),
        "source_count": len({snapshot.source_id for snapshot in snapshots}),
        "input_record_count": sum(len(snapshot.records) for snapshot in snapshots),
        "accepted_import_count": len(imports),
        "status_receipt_count": len(receipts),
        "quarantine_count": len(quarantined),
        "current_open_claim_count": sum(
            bool(row["current_open_status_claimed"]) for row in imports
        ),
        "solution_claim_count": sum(bool(row["solution_claimed"]) for row in imports),
        "records_requiring_refresh": sum(
            "requires_refresh" in str(row["status"]) for row in imports
        ),
        "source_retrieval_certified": False,
        "current_status_certification_claimed": False,
        "scientific_validation_claimed": False,
        "solution_claimed": False,
        "formal_proof_claimed": False,
        "permanent_total_cap": None,
        "manifest_digest": manifest["digest"],
    }
    report["digest"] = stable_digest({k: v for k, v in report.items() if k != "digest"})
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number}: row must be object")
        rows.append(value)
    return rows


def audit_source_bundle(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    errors: list[str] = []
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

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    manifest_payload = {k: v for k, v in manifest.items() if k != "digest"}
    if manifest.get("digest") != stable_digest(manifest_payload):
        errors.append("manifest digest mismatch")
    report_payload = {k: v for k, v in report.items() if k != "digest"}
    if report.get("digest") != stable_digest(report_payload):
        errors.append("report digest mismatch")

    manifest_artifacts = {item["path"]: item for item in manifest.get("artifacts", [])}
    for name in (
        "source_snapshots.jsonl",
        "imports.jsonl",
        "status_receipts.jsonl",
        "quarantine.jsonl",
    ):
        expected = manifest_artifacts.get(name)
        if expected is None:
            errors.append(f"manifest missing {name}")
            continue
        actual = _file_receipt(output / name)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected.get(field):
                errors.append(f"{name}: {field} mismatch")

    imports = _read_jsonl(output / "imports.jsonl")
    receipts = _read_jsonl(output / "status_receipts.jsonl")
    quarantined = _read_jsonl(output / "quarantine.jsonl")
    snapshots = _read_jsonl(output / "source_snapshots.jsonl")

    receipt_ids = {row.get("receipt_id") for row in receipts}
    snapshot_ids = {row.get("snapshot_id") for row in snapshots}
    for row in imports:
        if row.get("solution_claimed") is not False:
            errors.append(f"{row.get('problem_id')}: solution claim present")
        if row.get("status_receipt_id") not in receipt_ids:
            errors.append(f"{row.get('problem_id')}: missing status receipt")
        if row.get("source_snapshot_id") not in snapshot_ids:
            errors.append(f"{row.get('problem_id')}: missing source snapshot")
        if row.get("current_open_status_claimed"):
            if not row.get("source_verified_at"):
                errors.append(f"{row.get('problem_id')}: open claim lacks verification date")
            matching = [
                receipt for receipt in receipts
                if receipt.get("receipt_id") == row.get("status_receipt_id")
            ]
            if len(matching) != 1 or matching[0].get("claim_allowed") is not True:
                errors.append(f"{row.get('problem_id')}: open claim receipt not allowed")

    expected_counts = {
        "snapshot_count": len(snapshots),
        "input_record_count": len(receipts),
        "accepted_import_count": len(imports),
        "status_receipt_count": len(receipts),
        "quarantine_count": len(quarantined),
    }
    for field, actual in expected_counts.items():
        if report.get(field) != actual:
            errors.append(f"report {field}: expected {actual}, got {report.get(field)}")

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
        "import_count": len(imports),
        "receipt_count": len(receipts),
        "quarantine_count": len(quarantined),
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
        "current_status_certification_claimed": False,
    }
