"""R0.2 immutable GitHub Actions telemetry ingestion for Ω-WORKMAX-GIT-T∞."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from statistics import mean, median
from typing import Any, Iterable

def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    result = datetime.fromisoformat(text)
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)

def _seconds(a: str | None, b: str | None) -> float:
    start, end = _dt(a), _dt(b)
    if start is None or end is None:
        return 0.0
    return max(0.0, (end - start).total_seconds())

def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    data = sorted(float(v) for v in values)
    if len(data) == 1:
        return data[0]
    pos = (len(data) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(data) - 1)
    frac = pos - lo
    return data[lo] * (1.0 - frac) + data[hi] * frac

@dataclass(frozen=True)
class RunRecord:
    run_id: int
    attempt: int
    workflow_id: int
    workflow_name: str
    head_sha: str
    event: str
    status: str
    conclusion: str | None
    created_at: str | None
    run_started_at: str | None
    updated_at: str | None

    @property
    def identity(self) -> str:
        return f"{self.run_id}:{self.attempt}:{self.head_sha}"

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "RunRecord":
        return cls(
            run_id=int(item["id"]),
            attempt=int(item.get("run_attempt", 1)),
            workflow_id=int(item.get("workflow_id", 0)),
            workflow_name=str(item.get("name") or ""),
            head_sha=str(item.get("head_sha") or ""),
            event=str(item.get("event") or ""),
            status=str(item.get("status") or ""),
            conclusion=item.get("conclusion"),
            created_at=item.get("created_at"),
            run_started_at=item.get("run_started_at"),
            updated_at=item.get("updated_at"),
        )

@dataclass(frozen=True)
class JobRecord:
    job_id: int
    run_id: int
    name: str
    status: str
    conclusion: str | None
    created_at: str | None
    started_at: str | None
    completed_at: str | None

    @classmethod
    def from_dict(cls, run_id: int, item: dict[str, Any]) -> "JobRecord":
        return cls(
            job_id=int(item["id"]),
            run_id=int(run_id),
            name=str(item.get("name") or ""),
            status=str(item.get("status") or ""),
            conclusion=item.get("conclusion"),
            created_at=item.get("created_at"),
            started_at=item.get("started_at"),
            completed_at=item.get("completed_at"),
        )

def build_actions_snapshot(
    runs: Iterable[dict[str, Any]],
    jobs_by_run: dict[int | str, Iterable[dict[str, Any]]],
    *,
    observed_at: str,
) -> dict[str, Any]:
    run_map: dict[tuple[int, int], RunRecord] = {}
    for raw in runs:
        record = RunRecord.from_dict(raw)
        run_map[(record.run_id, record.attempt)] = record
    run_records = sorted(run_map.values(), key=lambda r: (r.run_id, r.attempt))

    job_map: dict[int, JobRecord] = {}
    for run in run_records:
        for raw in jobs_by_run.get(run.run_id, jobs_by_run.get(str(run.run_id), ())):
            job = JobRecord.from_dict(run.run_id, raw)
            job_map[job.job_id] = job
    jobs = sorted(job_map.values(), key=lambda j: j.job_id)

    queue_times = [_seconds(j.created_at, j.started_at) for j in jobs if j.started_at]
    exec_times = [_seconds(j.started_at, j.completed_at) for j in jobs if j.started_at and j.completed_at]
    cancelled = [r for r in run_records if r.conclusion == "cancelled"]
    queued = [r for r in run_records if r.status == "queued"]
    active = [r for r in run_records if r.status in {"queued", "in_progress"}]
    completed = [r for r in run_records if r.status == "completed"]

    by_workflow: dict[str, dict[str, Any]] = {}
    for run in run_records:
        bucket = by_workflow.setdefault(run.workflow_name, {"runs": 0, "cancelled": 0, "active": 0, "completed": 0})
        bucket["runs"] += 1
        bucket["cancelled"] += int(run.conclusion == "cancelled")
        bucket["active"] += int(run.status in {"queued", "in_progress"})
        bucket["completed"] += int(run.status == "completed")

    evidence = {
        "schema": "omega-workmax-actions-telemetry/v1",
        "observed_at": observed_at,
        "run_count": len(run_records),
        "job_count": len(jobs),
        "queued_run_count": len(queued),
        "active_run_count": len(active),
        "completed_run_count": len(completed),
        "cancelled_run_count": len(cancelled),
        "queue_seconds": {
            "samples": len(queue_times),
            "mean": mean(queue_times) if queue_times else 0.0,
            "p50": median(queue_times) if queue_times else 0.0,
            "p95": _quantile(queue_times, 0.95),
            "max": max(queue_times, default=0.0),
        },
        "execution_seconds": {
            "samples": len(exec_times),
            "mean": mean(exec_times) if exec_times else 0.0,
            "p50": median(exec_times) if exec_times else 0.0,
            "p95": _quantile(exec_times, 0.95),
            "max": max(exec_times, default=0.0),
        },
        "workflow_counts": dict(sorted(by_workflow.items())),
        "run_identities": [r.identity for r in run_records],
        "job_ids": [j.job_id for j in jobs],
        "head_shas": sorted({r.head_sha for r in run_records if r.head_sha}),
        "oak_limits": [
            "A queued snapshot is evidence of queue state at observed_at, not proof of long-term queue latency.",
            "Cancelled runs can indicate supersession or failure; cancellation cause must be inspected before classifying waste.",
            "Run/job timing is operational evidence, not proof that a topology change caused a speedup.",
            "The collector is offline and performs no GitHub network mutation.",
        ],
    }
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    evidence["snapshot_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return evidence
