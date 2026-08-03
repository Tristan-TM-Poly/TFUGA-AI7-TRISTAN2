"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.7."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_job_campaign
from .compiler import compile_job_campaign as _compile_job_campaign
from .model import BUNDLE_SCHEMA, RUNNER_KINDS, JobSpec, read_jsonl, stable_digest
from .runners import execute_job


def _normalize_report(output: Path) -> dict[str, Any]:
    report_path = output / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    # Operational history must not perturb the final scientific materialization.
    # Partial checkpoints remain identifiable through `complete` and counts.
    report.pop("resumed", None)
    report["digest"] = stable_digest({k: v for k, v in report.items() if k != "digest"})
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def compile_job_campaign(
    bundle_path: str | Path,
    output_dir: str | Path,
    *,
    max_jobs: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    output = Path(output_dir)
    _compile_job_campaign(bundle_path, output, max_jobs=max_jobs, resume=resume)
    return _normalize_report(output)


def replay_job(campaign_dir: str | Path, job_id: str) -> dict[str, Any]:
    output = Path(campaign_dir)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    specs = read_jsonl(output / "job_specs.jsonl")
    matches = [row for row in specs if row.get("job_id") == job_id]
    if len(matches) != 1:
        raise ValueError(f"job_id must identify exactly one job: {job_id}")
    job = JobSpec(**matches[0])
    replayed = execute_job(job, str(manifest["campaign_id"]), str(manifest["bundle_digest"]))
    stored = [
        row for row in read_jsonl(output / "job_receipts.jsonl")
        if row.get("job_id") == job_id
    ]
    stored_receipt = stored[0] if len(stored) == 1 else None
    result = {
        "schema": "omega-problem-job-replay/7",
        "campaign_id": manifest["campaign_id"],
        "job_id": job_id,
        "replayed_receipt": replayed,
        "stored_receipt_found": stored_receipt is not None,
        "matches_stored_receipt": stored_receipt == replayed if stored_receipt is not None else None,
        "network_access_used": False,
        "external_execution_used": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    result["replay_digest"] = stable_digest(result)
    return result


__all__ = [
    "BUNDLE_SCHEMA",
    "RUNNER_KINDS",
    "audit_job_campaign",
    "compile_job_campaign",
    "replay_job",
]
