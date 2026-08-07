from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

BUNDLE_SCHEMA = "omega-problem-job-bundle/7"
REPORT_SCHEMA = "omega-problem-job-report/7"
MANIFEST_SCHEMA = "omega-problem-job-manifest/7"
CHECKPOINT_SCHEMA = "omega-problem-job-checkpoint/7"

RUNNER_KINDS = {
    "exact_expression",
    "interval_polynomial",
    "sat_certificate",
    "lean_skeleton",
}

ERROR_CONTRACTS = {
    "exact",
    "outward_interval",
    "boolean_certificate",
    "structural_only",
}

FINAL_STATUSES = {
    "success",
    "failure",
    "invalid_certificate",
    "blocked",
}


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    canonical_problem_id: str
    claim_id: str | None
    runner_kind: str
    method: str
    scope: str
    stopping_rule: str
    deterministic_seed: int
    resource_limits: Mapping[str, int]
    error_contract: Mapping[str, Any]
    input: Mapping[str, Any]
    license_note: str
    network_access: bool
    external_execution: bool
    proof_claimed: bool
    solution_claimed: bool
    job_digest: str


@dataclass(frozen=True)
class JobBundle:
    campaign_id: str
    environment_lock: Mapping[str, Any]
    jobs: tuple[JobSpec, ...]
    bundle_digest: str


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number}: row must be an object")
        rows.append(value)
    return rows


def file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "rows": sum(1 for line in data.splitlines() if line.strip()),
    }


def _identifier(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:\-]*", result):
        raise ValueError(f"invalid {field}: {result!r}")
    return result


def _positive_limit(raw: Mapping[str, Any], name: str, maximum: int) -> int:
    value = raw.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ValueError(f"resource_limits.{name} must be an integer in [1, {maximum}]")
    return value


def load_job_bundle(path_like: str | Path) -> JobBundle:
    path = Path(path_like)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BUNDLE_SCHEMA:
        raise ValueError(f"{path}: unsupported bundle schema")
    campaign_id = _identifier(payload.get("campaign_id"), "campaign_id")
    environment_lock = payload.get("environment_lock")
    if not isinstance(environment_lock, Mapping):
        raise ValueError(f"{path}: environment_lock must be an object")
    if environment_lock.get("network_access") is not False:
        raise ValueError(f"{path}: environment lock must disable network access")
    if environment_lock.get("arbitrary_subprocess") is not False:
        raise ValueError(f"{path}: environment lock must disable arbitrary subprocesses")
    if not str(environment_lock.get("contract_version", "")).strip():
        raise ValueError(f"{path}: environment lock requires contract_version")

    jobs_raw = payload.get("jobs")
    if not isinstance(jobs_raw, list) or not all(isinstance(item, Mapping) for item in jobs_raw):
        raise ValueError(f"{path}: jobs must be an object list")
    jobs: list[JobSpec] = []
    for raw in jobs_raw:
        job_id = _identifier(raw.get("job_id"), "job_id")
        canonical_problem_id = _identifier(raw.get("canonical_problem_id"), "canonical_problem_id")
        claim_raw = raw.get("claim_id")
        claim_id = _identifier(claim_raw, "claim_id") if claim_raw is not None else None
        runner_kind = str(raw.get("runner_kind", "")).strip()
        if runner_kind not in RUNNER_KINDS:
            raise ValueError(f"{job_id}: unsupported runner_kind {runner_kind!r}")
        method = str(raw.get("method", "")).strip()
        scope = str(raw.get("scope", "")).strip()
        stopping_rule = str(raw.get("stopping_rule", "")).strip()
        license_note = str(raw.get("license_note", "")).strip()
        if not all((method, scope, stopping_rule, license_note)):
            raise ValueError(f"{job_id}: method, scope, stopping_rule and license_note are required")
        seed = raw.get("deterministic_seed", 0)
        if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise ValueError(f"{job_id}: deterministic_seed must be a nonnegative integer")
        resource_raw = raw.get("resource_limits")
        if not isinstance(resource_raw, Mapping):
            raise ValueError(f"{job_id}: resource_limits must be an object")
        resource_limits = {
            "max_operations": _positive_limit(resource_raw, "max_operations", 1_000_000),
            "max_output_bytes": _positive_limit(resource_raw, "max_output_bytes", 1_000_000),
            "max_input_bytes": _positive_limit(resource_raw, "max_input_bytes", 1_000_000),
        }
        error_contract_raw = raw.get("error_contract")
        if not isinstance(error_contract_raw, Mapping):
            raise ValueError(f"{job_id}: error_contract must be an object")
        error_contract = dict(error_contract_raw)
        if error_contract.get("kind") not in ERROR_CONTRACTS:
            raise ValueError(f"{job_id}: unsupported error contract")
        input_raw = raw.get("input")
        if not isinstance(input_raw, Mapping):
            raise ValueError(f"{job_id}: input must be an object")
        input_payload = dict(input_raw)
        if len(json.dumps(input_payload, ensure_ascii=False).encode("utf-8")) > resource_limits["max_input_bytes"]:
            raise ValueError(f"{job_id}: input exceeds max_input_bytes")
        network_access = bool(raw.get("network_access", False))
        external_execution = bool(raw.get("external_execution", False))
        if network_access:
            raise ValueError(f"{job_id}: network access is forbidden")
        if external_execution:
            raise ValueError(f"{job_id}: external execution is forbidden")
        proof_claimed = bool(raw.get("proof_claimed", False))
        solution_claimed = bool(raw.get("solution_claimed", False))
        if proof_claimed or solution_claimed:
            raise ValueError(f"{job_id}: proof and solution claims are forbidden in job ingestion")
        base = {
            "job_id": job_id,
            "canonical_problem_id": canonical_problem_id,
            "claim_id": claim_id,
            "runner_kind": runner_kind,
            "method": method,
            "scope": scope,
            "stopping_rule": stopping_rule,
            "deterministic_seed": seed,
            "resource_limits": resource_limits,
            "error_contract": error_contract,
            "input": input_payload,
            "license_note": license_note,
            "network_access": False,
            "external_execution": False,
            "proof_claimed": False,
            "solution_claimed": False,
        }
        jobs.append(JobSpec(**base, job_digest=stable_digest(base)))
    jobs.sort(key=lambda item: item.job_id)
    if len({job.job_id for job in jobs}) != len(jobs):
        raise ValueError(f"{path}: duplicate job_id")
    bundle_base = {
        "schema": BUNDLE_SCHEMA,
        "campaign_id": campaign_id,
        "environment_lock": dict(environment_lock),
        "jobs": [
            {key: value for key, value in job.__dict__.items() if key != "job_digest"}
            for job in jobs
        ],
    }
    return JobBundle(
        campaign_id=campaign_id,
        environment_lock=dict(environment_lock),
        jobs=tuple(jobs),
        bundle_digest=stable_digest(bundle_base),
    )
