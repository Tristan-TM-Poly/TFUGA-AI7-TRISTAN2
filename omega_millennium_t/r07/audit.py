from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .compiler import _build_events, _build_mminus
from .model import JobBundle, JobSpec, file_receipt, read_jsonl, stable_digest
from .runners import execute_job


def audit_job_campaign(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "job_specs.jsonl",
        "job_receipts.jsonl",
        "campaign_events.jsonl",
        "mminus_records.jsonl",
        "checkpoint.json",
        "manifest.json",
        "report.json",
    }
    missing = sorted(name for name in required if not (output / name).exists())
    if missing:
        return {
            "schema": "omega-problem-job-audit/7",
            "valid": False,
            "errors": [f"missing artifact: {name}" for name in missing],
            "solution_claimed": False,
        }

    errors: list[str] = []
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((output / "checkpoint.json").read_text(encoding="utf-8"))
    if manifest.get("digest") != stable_digest({k: v for k, v in manifest.items() if k != "digest"}):
        errors.append("manifest digest mismatch")
    if report.get("digest") != stable_digest({k: v for k, v in report.items() if k != "digest"}):
        errors.append("report digest mismatch")
    if checkpoint.get("checkpoint_digest") != stable_digest(
        {k: v for k, v in checkpoint.items() if k != "checkpoint_digest"}
    ):
        errors.append("checkpoint digest mismatch")

    manifest_artifacts = {item["path"]: item for item in manifest.get("artifacts", [])}
    for name in required - {"manifest.json", "report.json"}:
        expected = manifest_artifacts.get(name)
        if expected is None:
            errors.append(f"manifest missing {name}")
            continue
        actual = file_receipt(output / name)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected.get(field):
                errors.append(f"{name}: {field} mismatch")

    spec_rows = read_jsonl(output / "job_specs.jsonl")
    receipts = read_jsonl(output / "job_receipts.jsonl")
    events = read_jsonl(output / "campaign_events.jsonl")
    mminus = read_jsonl(output / "mminus_records.jsonl")

    jobs: list[JobSpec] = []
    for row in spec_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "job_digest"})
        if row.get("job_digest") != expected:
            errors.append(f"{row.get('job_id')}: job digest mismatch")
        try:
            jobs.append(JobSpec(**row))
        except TypeError as exc:
            errors.append(f"{row.get('job_id')}: invalid job shape: {exc}")
    jobs.sort(key=lambda item: item.job_id)
    if len({job.job_id for job in jobs}) != len(jobs):
        errors.append("duplicate job_id")

    campaign_id = str(manifest.get("campaign_id", ""))
    bundle_digest = str(manifest.get("bundle_digest", ""))
    bundle = JobBundle(
        campaign_id=campaign_id,
        environment_lock=dict(manifest.get("environment_lock", {})),
        jobs=tuple(jobs),
        bundle_digest=bundle_digest,
    )
    if manifest.get("environment_lock_digest") != stable_digest(bundle.environment_lock):
        errors.append("environment lock digest mismatch")

    receipt_ids: set[str] = set()
    receipt_by_id: dict[str, dict[str, Any]] = {}
    job_by_id = {job.job_id: job for job in jobs}
    for receipt in receipts:
        job_id = str(receipt.get("job_id", ""))
        if job_id in receipt_ids:
            errors.append(f"{job_id}: duplicate receipt")
            continue
        receipt_ids.add(job_id)
        receipt_by_id[job_id] = receipt
        if job_id not in job_by_id:
            errors.append(f"{job_id}: receipt references unknown job")
            continue
        expected_digest = stable_digest({k: v for k, v in receipt.items() if k != "receipt_digest"})
        if receipt.get("receipt_digest") != expected_digest:
            errors.append(f"{job_id}: receipt digest mismatch")
        replayed = execute_job(job_by_id[job_id], campaign_id, bundle_digest)
        if receipt != replayed:
            errors.append(f"{job_id}: receipt differs from deterministic replay")
        if receipt.get("network_access") is not False or receipt.get("external_execution") is not False:
            errors.append(f"{job_id}: forbidden execution capability recorded")
        if receipt.get("theorem_promotion_allowed") is not False:
            errors.append(f"{job_id}: theorem promotion must be false")
        if receipt.get("proof_claimed") is not False or receipt.get("solution_claimed") is not False:
            errors.append(f"{job_id}: forbidden proof or solution claim")

    expected_completed = [job.job_id for job in jobs[: len(receipts)]]
    if sorted(receipt_ids) != sorted(expected_completed):
        errors.append("completed jobs must form the deterministic campaign prefix")
    remaining_ids = [job.job_id for job in jobs if job.job_id not in receipt_ids]
    complete = not remaining_ids

    recomputed_events = _build_events(bundle, receipts, complete)
    if events != recomputed_events:
        errors.append("campaign events do not match deterministic reconstruction")
    for event in events:
        expected = stable_digest({k: v for k, v in event.items() if k != "event_digest"})
        if event.get("event_digest") != expected:
            errors.append(f"{event.get('event_id')}: event digest mismatch")

    recomputed_mminus = _build_mminus(receipts)
    if mminus != recomputed_mminus:
        errors.append("M-minus records do not match deterministic reconstruction")
    for row in mminus:
        expected = stable_digest({k: v for k, v in row.items() if k != "mminus_digest"})
        if row.get("mminus_digest") != expected:
            errors.append(f"{row.get('mminus_id')}: M-minus digest mismatch")
        if row.get("immutable") is not True:
            errors.append(f"{row.get('mminus_id')}: M-minus must be immutable")

    expected_checkpoint = {
        "campaign_id": campaign_id,
        "bundle_digest": bundle_digest,
        "environment_lock_digest": stable_digest(bundle.environment_lock),
        "status": "complete" if complete else "partial",
        "completed_job_ids": sorted(receipt_ids),
        "remaining_job_ids": remaining_ids,
        "completed_job_count": len(receipts),
        "remaining_job_count": len(remaining_ids),
        "permanent_total_cap": None,
    }
    for field, expected in expected_checkpoint.items():
        if checkpoint.get(field) != expected:
            errors.append(f"checkpoint {field}: expected {expected!r}, got {checkpoint.get(field)!r}")

    status_counts = {
        status: sum(receipt.get("status") == status for receipt in receipts)
        for status in ("success", "failure", "invalid_certificate", "blocked")
    }
    expected_report = {
        "job_count": len(jobs),
        "completed_job_count": len(receipts),
        "remaining_job_count": len(remaining_ids),
        "event_count": len(events),
        "mminus_record_count": len(mminus),
        "status_counts": status_counts,
        "runner_kinds": sorted({job.runner_kind for job in jobs}),
        "complete": complete,
        "checkpoint_digest": checkpoint.get("checkpoint_digest"),
        "manifest_digest": manifest.get("digest"),
    }
    for field, expected in expected_report.items():
        if report.get(field) != expected:
            errors.append(f"report {field}: expected {expected!r}, got {report.get(field)!r}")

    if manifest.get("network_access_allowed") is not False:
        errors.append("manifest must forbid network access")
    if manifest.get("arbitrary_subprocess_allowed") is not False:
        errors.append("manifest must forbid arbitrary subprocesses")
    if manifest.get("certificate_generator_is_verifier") is not False:
        errors.append("certificate generator and verifier must remain distinct")
    if manifest.get("numerical_theorem_promotion_allowed") is not False:
        errors.append("manifest must forbid numerical theorem promotion")
    for field in ("network_access_used", "external_execution_used", "proof_claimed", "solution_claimed", "scientific_validation_claimed"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    if report.get("theorem_promotion_count") != 0:
        errors.append("theorem_promotion_count must be zero")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")

    return {
        "schema": "omega-problem-job-audit/7",
        "valid": not errors,
        "errors": errors,
        "campaign_id": campaign_id,
        "job_count": len(jobs),
        "completed_job_count": len(receipts),
        "remaining_job_count": len(remaining_ids),
        "mminus_record_count": len(mminus),
        "complete": complete,
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
    }
