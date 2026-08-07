"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.7."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_job_campaign as _audit_job_campaign
from .compiler import compile_job_campaign as _compile_job_campaign
from .model import BUNDLE_SCHEMA, RUNNER_KINDS, JobSpec, read_jsonl, stable_digest
from .runners import execute_job

EXPECTED_ERROR_CONTRACT = {
    "exact_expression": "exact",
    "interval_polynomial": "outward_interval",
    "sat_certificate": "boolean_certificate",
    "lean_skeleton": "structural_only",
}


def _validate_runner_contracts(bundle_path: Path) -> None:
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if payload.get("schema") != BUNDLE_SCHEMA:
        raise ValueError(f"{bundle_path}: unsupported bundle schema")
    for raw in payload.get("jobs", []):
        if not isinstance(raw, dict):
            raise ValueError(f"{bundle_path}: every job must be an object")
        runner_kind = str(raw.get("runner_kind", ""))
        error_contract = raw.get("error_contract")
        expected = EXPECTED_ERROR_CONTRACT.get(runner_kind)
        actual = error_contract.get("kind") if isinstance(error_contract, dict) else None
        if expected is not None and actual != expected:
            raise ValueError(
                f"{raw.get('job_id', 'unknown')}: runner {runner_kind} requires "
                f"error_contract.kind={expected!r}, got {actual!r}"
            )


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
    bundle = Path(bundle_path)
    _validate_runner_contracts(bundle)
    output = Path(output_dir)
    _compile_job_campaign(bundle, output, max_jobs=max_jobs, resume=resume)
    return _normalize_report(output)


def audit_job_campaign(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    result = _audit_job_campaign(output)
    errors = list(result.get("errors", []))
    manifest_path = output / "manifest.json"
    report_path = output / "report.json"
    specs_path = output / "job_specs.jsonl"
    if manifest_path.exists() and report_path.exists() and specs_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        specs = read_jsonl(specs_path)
        normalized_jobs = [
            {key: value for key, value in row.items() if key != "job_digest"}
            for row in sorted(specs, key=lambda row: str(row.get("job_id", "")))
        ]
        bundle_base = {
            "schema": BUNDLE_SCHEMA,
            "campaign_id": manifest.get("campaign_id"),
            "environment_lock": manifest.get("environment_lock", {}),
            "jobs": normalized_jobs,
        }
        recomputed_bundle_digest = stable_digest(bundle_base)
        if manifest.get("bundle_digest") != recomputed_bundle_digest:
            errors.append("bundle digest does not match materialized job specs")
        if report.get("bundle_digest") != recomputed_bundle_digest:
            errors.append("report bundle digest mismatch")
        for row in specs:
            runner_kind = str(row.get("runner_kind", ""))
            actual = row.get("error_contract", {}).get("kind") if isinstance(row.get("error_contract"), dict) else None
            expected = EXPECTED_ERROR_CONTRACT.get(runner_kind)
            if expected is None or actual != expected:
                errors.append(
                    f"{row.get('job_id')}: materialized runner/error contract mismatch"
                )
    result["errors"] = errors
    result["valid"] = not errors
    return result


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
