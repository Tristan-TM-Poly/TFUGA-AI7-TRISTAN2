"""Empirical telemetry layer for Ω-ACTIONS-T∞.

The core stays network-free: it ingests JSON exported from the GitHub Actions API
and derives reproducible run/job metrics, failure localization and supersession
signals. Network collection, when desired, lives in a GitHub workflow.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _parse_time(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _seconds(start: Any, end: Any) -> float | None:
    left = _parse_time(start)
    right = _parse_time(end)
    if left is None or right is None or right < left:
        return None
    return round((right - left).total_seconds(), 3)


def _percentile(values: Iterable[float], q: float) -> float | None:
    ordered = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not ordered:
        return None
    if len(ordered) == 1:
        return round(ordered[0], 3)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return round(ordered[lo], 3)
    value = ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)
    return round(value, 3)


def _summary(values: Iterable[float]) -> dict[str, float | int | None]:
    data = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return {
        "count": len(data),
        "p50": _percentile(data, 0.50),
        "p95": _percentile(data, 0.95),
        "max": round(max(data), 3) if data else None,
        "mean": round(sum(data) / len(data), 3) if data else None,
    }


def _runs_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("workflow_runs", "runs"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if "id" in payload:
        return [payload]
    return []


def _snapshot_time(runs: list[dict[str, Any]]) -> datetime:
    candidates: list[datetime] = []
    for run in runs:
        for key in ("updated_at", "completed_at", "run_started_at", "created_at"):
            dt = _parse_time(run.get(key))
            if dt:
                candidates.append(dt)
        for job in run.get("jobs") or []:
            if not isinstance(job, dict):
                continue
            for key in ("completed_at", "started_at", "created_at"):
                dt = _parse_time(job.get(key))
                if dt:
                    candidates.append(dt)
    return max(candidates) if candidates else datetime.now(timezone.utc)


def _run_key(run: dict[str, Any]) -> tuple[str, str]:
    workflow = str(run.get("name") or run.get("workflow_name") or run.get("path") or run.get("workflow_id") or "unknown")
    branch = str(run.get("head_branch") or run.get("ref") or "")
    return workflow, branch


def _job_duration(job: dict[str, Any]) -> float | None:
    return _seconds(job.get("started_at"), job.get("completed_at"))


def _step_duration(step: dict[str, Any]) -> float | None:
    return _seconds(step.get("started_at"), step.get("completed_at"))


def analyze_telemetry(payload: Any) -> dict[str, Any]:
    """Analyze exported GitHub Actions run/job telemetry deterministically."""
    runs = _runs_from_payload(payload)
    snapshot = _snapshot_time(runs)

    queue_times: list[float] = []
    run_durations: list[float] = []
    workflow_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "run_count": 0, "success": 0, "failure": 0, "cancelled": 0, "other": 0,
        "queue_seconds": [], "duration_seconds": [],
    })
    job_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "count": 0, "success": 0, "failure": 0, "cancelled": 0, "other": 0,
        "duration_seconds": [], "step_duration_seconds": [],
    })
    states: dict[str, int] = defaultdict(int)
    conclusions: dict[str, int] = defaultdict(int)
    run_rows: list[dict[str, Any]] = []

    for run in runs:
        name = str(run.get("name") or run.get("workflow_name") or run.get("path") or run.get("workflow_id") or "unknown")
        status = str(run.get("status") or "unknown")
        conclusion = str(run.get("conclusion") or "none")
        states[status] += 1
        conclusions[conclusion] += 1
        started = run.get("run_started_at") or run.get("started_at")
        created = run.get("created_at")
        completed = run.get("completed_at") or run.get("updated_at")
        queue = _seconds(created, started)
        duration = _seconds(started, completed)
        if queue is not None:
            queue_times.append(queue)
        if duration is not None and status == "completed":
            run_durations.append(duration)

        ws = workflow_stats[name]
        ws["run_count"] += 1
        if conclusion in {"success", "failure", "cancelled"}:
            ws[conclusion] += 1
        else:
            ws["other"] += 1
        if queue is not None:
            ws["queue_seconds"].append(queue)
        if duration is not None and status == "completed":
            ws["duration_seconds"].append(duration)

        jobs = [job for job in (run.get("jobs") or []) if isinstance(job, dict)]
        failed_jobs: list[str] = []
        for job in jobs:
            job_name = str(job.get("name") or "unknown")
            jc = str(job.get("conclusion") or "none")
            js = job_stats[job_name]
            js["count"] += 1
            if jc in {"success", "failure", "cancelled"}:
                js[jc] += 1
            else:
                js["other"] += 1
            jd = _job_duration(job)
            if jd is not None:
                js["duration_seconds"].append(jd)
            for step in job.get("steps") or []:
                if isinstance(step, dict):
                    sd = _step_duration(step)
                    if sd is not None:
                        js["step_duration_seconds"].append(sd)
            if jc == "failure":
                failed_jobs.append(job_name)

        run_rows.append({
            "id": run.get("id"), "name": name, "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"), "event": run.get("event"), "status": status,
            "conclusion": conclusion, "created_at": created, "started_at": started,
            "completed_at": completed, "queue_seconds": queue, "duration_seconds": duration,
            "job_count": len(jobs), "failed_jobs": sorted(failed_jobs),
        })

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[_run_key(run)].append(run)

    superseded: list[dict[str, Any]] = []
    for (workflow, branch), group in grouped.items():
        ordered = sorted(group, key=lambda r: _parse_time(r.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc))
        for index, run in enumerate(ordered[:-1]):
            if str(run.get("status")) not in {"queued", "in_progress", "waiting", "pending", "requested"}:
                continue
            newer = ordered[index + 1 :]
            start = _parse_time(run.get("run_started_at") or run.get("started_at") or run.get("created_at"))
            active_age = round((snapshot - start).total_seconds(), 3) if start and snapshot >= start else None
            superseded.append({
                "workflow": workflow, "branch": branch, "run_id": run.get("id"),
                "newer_run_id": newer[-1].get("id"), "status": run.get("status"),
                "active_age_seconds_at_snapshot": active_age,
            })

    workflows_out: list[dict[str, Any]] = []
    for name, stat in sorted(workflow_stats.items(), key=lambda item: (-item[1]["run_count"], item[0])):
        completed = stat["success"] + stat["failure"] + stat["cancelled"]
        workflows_out.append({
            "name": name, "run_count": stat["run_count"], "success": stat["success"],
            "failure": stat["failure"], "cancelled": stat["cancelled"], "other": stat["other"],
            "failure_rate_completed": round(stat["failure"] / completed, 4) if completed else None,
            "queue_seconds": _summary(stat["queue_seconds"]),
            "duration_seconds": _summary(stat["duration_seconds"]),
        })

    jobs_out: list[dict[str, Any]] = []
    for name, stat in sorted(job_stats.items(), key=lambda item: (-item[1]["count"], item[0])):
        completed = stat["success"] + stat["failure"] + stat["cancelled"]
        jobs_out.append({
            "name": name, "count": stat["count"], "success": stat["success"],
            "failure": stat["failure"], "cancelled": stat["cancelled"], "other": stat["other"],
            "failure_rate_completed": round(stat["failure"] / completed, 4) if completed else None,
            "duration_seconds": _summary(stat["duration_seconds"]),
            "step_duration_seconds": _summary(stat["step_duration_seconds"]),
        })

    completed_runs = sum(1 for r in runs if str(r.get("status")) == "completed")
    failures = sum(1 for r in runs if str(r.get("conclusion")) == "failure")
    recommendations: list[dict[str, Any]] = []
    if superseded:
        recommendations.append({
            "id": "empirical-cancel-obsolete-runs", "priority": "high",
            "evidence": {"superseded_active_runs": len(superseded)},
            "message": "Active runs were superseded by newer runs for the same workflow/branch; evaluate concurrency cancel-in-progress.",
        })
    q95 = _percentile(queue_times, 0.95)
    if q95 is not None and q95 >= 30:
        recommendations.append({
            "id": "queue-capacity-or-fanout", "priority": "high" if q95 >= 120 else "medium",
            "evidence": {"queue_p95_seconds": q95},
            "message": "Queue latency is material; reduce fan-out and obsolete work before adding runner capacity.",
        })
    noisy = [w for w in workflows_out if w["run_count"] >= 5 and (w["failure_rate_completed"] or 0) >= 0.20]
    if noisy:
        recommendations.append({
            "id": "failure-localization", "priority": "medium",
            "evidence": {"workflows": [w["name"] for w in noisy[:10]]},
            "message": "High-failure workflows should move fast deterministic checks earlier and isolate flaky/expensive stages.",
        })

    return {
        "schema": "omega-actions-telemetry/v0.2",
        "snapshot_at": snapshot.isoformat().replace("+00:00", "Z"),
        "aggregate": {
            "run_count": len(runs), "completed_runs": completed_runs,
            "active_runs": len(runs) - completed_runs, "failure_count": failures,
            "failure_rate_completed": round(failures / completed_runs, 4) if completed_runs else None,
            "queue_seconds": _summary(queue_times), "duration_seconds": _summary(run_durations),
            "workflow_count": len(workflow_stats), "job_name_count": len(job_stats),
            "superseded_active_runs": len(superseded),
            "superseded_active_age_seconds": round(sum(item["active_age_seconds_at_snapshot"] or 0 for item in superseded), 3),
        },
        "states": dict(sorted(states.items())), "conclusions": dict(sorted(conclusions.items())),
        "workflows": workflows_out, "jobs": jobs_out, "runs": run_rows,
        "superseded_active_runs": superseded, "recommendations": recommendations,
        "oak_limits": [
            "Telemetry is observational: correlation does not prove a proposed optimization caused latency or failures.",
            "Run duration is not identical to critical-path compute; runner queueing and parallel jobs can overlap.",
            "Active-run supersession is a cancellation candidate, not permission to cancel protected or release work.",
            "Before/after promotion requires comparable workloads and repeated samples or explicit uncertainty.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Ω-ACTIONS-T∞ — Empirical Telemetry", "",
        f"- Runs: **{a['run_count']}**", f"- Completed: **{a['completed_runs']}**",
        f"- Active: **{a['active_runs']}**", f"- Workflows observed: **{a['workflow_count']}**",
        f"- Queue p50 / p95: **{a['queue_seconds']['p50']} / {a['queue_seconds']['p95']} s**",
        f"- Duration p50 / p95: **{a['duration_seconds']['p50']} / {a['duration_seconds']['p95']} s**",
        f"- Superseded active runs: **{a['superseded_active_runs']}**", "", "## Recommendations", "",
    ]
    if report["recommendations"]:
        for item in report["recommendations"]:
            lines.append(f"- **{item['priority']} · {item['id']}** — {item['message']}")
    else:
        lines.append("- No empirical recommendation triggered by the current sample.")
    lines += ["", "## Highest-volume workflows", ""]
    for workflow in report["workflows"][:15]:
        lines.append(f"- `{workflow['name']}` — runs={workflow['run_count']}, failure_rate={workflow['failure_rate_completed']}, p95={workflow['duration_seconds']['p95']}s")
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in report["oak_limits"])
    return "\n".join(lines) + "\n"


def write_telemetry_report(input_path: str | Path, *, json_out: str | Path | None = None, markdown_out: str | Path | None = None) -> dict[str, Any]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    report = analyze_telemetry(payload)
    if json_out:
        Path(json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_out:
        Path(markdown_out).write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-telemetry", description="Analyze exported GitHub Actions telemetry.")
    parser.add_argument("input", help="JSON export containing workflow_runs enriched with optional jobs")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)
    report = write_telemetry_report(args.input, json_out=args.json_out, markdown_out=args.markdown_out)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        a = report["aggregate"]
        print(f"Ω-ACTIONS-T∞ telemetry runs={a['run_count']} workflows={a['workflow_count']} queue_p95={a['queue_seconds']['p95']}s duration_p95={a['duration_seconds']['p95']}s superseded_active={a['superseded_active_runs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
