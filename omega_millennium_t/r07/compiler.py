from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    CHECKPOINT_SCHEMA,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    JobBundle,
    JobSpec,
    file_receipt,
    load_job_bundle,
    read_jsonl,
    stable_digest,
    write_jsonl,
)
from .runners import execute_job


def _build_events(bundle: JobBundle, receipts: Sequence[Mapping[str, Any]], complete: bool) -> list[dict[str, Any]]:
    receipt_by_id = {str(row["job_id"]): row for row in receipts}
    events: list[dict[str, Any]] = []

    def add(event_type: str, job_id: str | None, payload: Mapping[str, Any]) -> None:
        row = {
            "event_id": f"event::{len(events) + 1:08d}",
            "logical_sequence": len(events) + 1,
            "campaign_id": bundle.campaign_id,
            "event_type": event_type,
            "job_id": job_id,
            "payload": dict(payload),
        }
        row["event_digest"] = stable_digest(row)
        events.append(row)

    add("campaign_started", None, {
        "bundle_digest": bundle.bundle_digest,
        "job_count": len(bundle.jobs),
        "environment_lock_digest": stable_digest(bundle.environment_lock),
    })
    for job in bundle.jobs:
        if job.job_id not in receipt_by_id:
            continue
        receipt = receipt_by_id[job.job_id]
        add("job_scheduled", job.job_id, {
            "runner_kind": job.runner_kind,
            "job_digest": job.job_digest,
        })
        add("job_completed", job.job_id, {
            "status": receipt["status"],
            "receipt_digest": receipt["receipt_digest"],
            "output_digest": receipt["output_digest"],
        })
    add("campaign_completed" if complete else "campaign_checkpointed", None, {
        "completed_job_count": len(receipts),
        "remaining_job_count": len(bundle.jobs) - len(receipts),
    })
    return events


def _build_mminus(receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for receipt in sorted(receipts, key=lambda row: str(row["job_id"])):
        status = str(receipt["status"])
        if status == "success":
            continue
        row = {
            "mminus_id": f"mminus::job::{receipt['job_id']}",
            "campaign_id": receipt["campaign_id"],
            "job_id": receipt["job_id"],
            "canonical_problem_id": receipt["canonical_problem_id"],
            "claim_id": receipt.get("claim_id"),
            "reason_type": status,
            "receipt_digest": receipt["receipt_digest"],
            "error_summary": receipt.get("stderr", "") or receipt.get("output", {}).get("error", ""),
            "immutable": True,
        }
        row["mminus_digest"] = stable_digest(row)
        rows.append(row)
    return rows


def _load_resume_state(output: Path, bundle: JobBundle) -> list[dict[str, Any]]:
    checkpoint_path = output / "checkpoint.json"
    receipts_path = output / "job_receipts.jsonl"
    if not checkpoint_path.exists() or not receipts_path.exists():
        raise ValueError("resume requires checkpoint.json and job_receipts.jsonl")
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("unsupported checkpoint schema")
    expected_checkpoint_digest = stable_digest({k: v for k, v in checkpoint.items() if k != "checkpoint_digest"})
    if checkpoint.get("checkpoint_digest") != expected_checkpoint_digest:
        raise ValueError("checkpoint digest mismatch")
    if checkpoint.get("campaign_id") != bundle.campaign_id:
        raise ValueError("checkpoint campaign mismatch")
    if checkpoint.get("bundle_digest") != bundle.bundle_digest:
        raise ValueError("checkpoint bundle digest mismatch")
    receipts = read_jsonl(receipts_path)
    known_jobs = {job.job_id: job for job in bundle.jobs}
    seen: set[str] = set()
    for receipt in receipts:
        job_id = str(receipt.get("job_id", ""))
        if job_id in seen or job_id not in known_jobs:
            raise ValueError(f"invalid resumed job receipt: {job_id}")
        seen.add(job_id)
        if receipt.get("job_digest") != known_jobs[job_id].job_digest:
            raise ValueError(f"{job_id}: resumed job digest mismatch")
        expected = stable_digest({k: v for k, v in receipt.items() if k != "receipt_digest"})
        if receipt.get("receipt_digest") != expected:
            raise ValueError(f"{job_id}: resumed receipt digest mismatch")
    if sorted(checkpoint.get("completed_job_ids", [])) != sorted(seen):
        raise ValueError("checkpoint completed_job_ids mismatch")
    return receipts


def compile_job_campaign(
    bundle_path: str | Path,
    output_dir: str | Path,
    *,
    max_jobs: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    bundle = load_job_bundle(bundle_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if max_jobs is not None and (not isinstance(max_jobs, int) or isinstance(max_jobs, bool) or max_jobs < 0):
        raise ValueError("max_jobs must be a nonnegative integer or null")

    receipts: list[dict[str, Any]] = _load_resume_state(output, bundle) if resume else []
    completed_ids = {str(row["job_id"]) for row in receipts}
    pending = [job for job in bundle.jobs if job.job_id not in completed_ids]
    selected = pending if max_jobs is None else pending[:max_jobs]
    for job in selected:
        receipts.append(execute_job(job, bundle.campaign_id, bundle.bundle_digest))
    receipts.sort(key=lambda row: str(row["job_id"]))
    completed_ids = {str(row["job_id"]) for row in receipts}
    remaining_ids = [job.job_id for job in bundle.jobs if job.job_id not in completed_ids]
    complete = not remaining_ids

    job_rows = [asdict(job) for job in bundle.jobs]
    events = _build_events(bundle, receipts, complete)
    mminus = _build_mminus(receipts)
    write_jsonl(output / "job_specs.jsonl", job_rows)
    write_jsonl(output / "job_receipts.jsonl", receipts)
    write_jsonl(output / "campaign_events.jsonl", events)
    write_jsonl(output / "mminus_records.jsonl", mminus)

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "campaign_id": bundle.campaign_id,
        "bundle_digest": bundle.bundle_digest,
        "environment_lock_digest": stable_digest(bundle.environment_lock),
        "status": "complete" if complete else "partial",
        "completed_job_ids": sorted(completed_ids),
        "remaining_job_ids": remaining_ids,
        "completed_job_count": len(completed_ids),
        "remaining_job_count": len(remaining_ids),
        "runtime_batch_limit": max_jobs,
        "permanent_total_cap": None,
    }
    checkpoint["checkpoint_digest"] = stable_digest(checkpoint)
    (output / "checkpoint.json").write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    artifact_names = (
        "job_specs.jsonl",
        "job_receipts.jsonl",
        "campaign_events.jsonl",
        "mminus_records.jsonl",
        "checkpoint.json",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "campaign_id": bundle.campaign_id,
        "bundle_digest": bundle.bundle_digest,
        "environment_lock": dict(bundle.environment_lock),
        "environment_lock_digest": stable_digest(bundle.environment_lock),
        "artifacts": [file_receipt(output / name) for name in artifact_names],
        "network_access_allowed": False,
        "arbitrary_subprocess_allowed": False,
        "certificate_generator_is_verifier": False,
        "numerical_theorem_promotion_allowed": False,
        "permanent_total_cap": None,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    manifest["digest"] = stable_digest({k: v for k, v in manifest.items() if k != "digest"})
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    status_counts = {
        status: sum(receipt["status"] == status for receipt in receipts)
        for status in ("success", "failure", "invalid_certificate", "blocked")
    }
    report = {
        "schema": REPORT_SCHEMA,
        "status": "CERTIFIED_OFFLINE_JOB_RUNNER_FIXTURE_R0_7" if complete else "PARTIAL_CHECKPOINT_R0_7",
        "campaign_id": bundle.campaign_id,
        "bundle_digest": bundle.bundle_digest,
        "job_count": len(bundle.jobs),
        "completed_job_count": len(receipts),
        "remaining_job_count": len(remaining_ids),
        "event_count": len(events),
        "mminus_record_count": len(mminus),
        "status_counts": status_counts,
        "runner_kinds": sorted({job.runner_kind for job in bundle.jobs}),
        "complete": complete,
        "resumed": resume,
        "runtime_batch_limit": max_jobs,
        "network_access_used": False,
        "external_execution_used": False,
        "theorem_promotion_count": 0,
        "proof_claimed": False,
        "solution_claimed": False,
        "scientific_validation_claimed": False,
        "permanent_total_cap": None,
        "checkpoint_digest": checkpoint["checkpoint_digest"],
        "manifest_digest": manifest["digest"],
    }
    report["digest"] = stable_digest({k: v for k, v in report.items() if k != "digest"})
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
