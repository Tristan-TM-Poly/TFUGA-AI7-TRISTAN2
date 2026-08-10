"""CI Digital Twin scheduling kernels for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _job_map(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(job["name"]): job for job in workflow.get("jobs", []) if isinstance(job, dict) and job.get("name")}


def _durations(workflow: dict[str, Any], duration_by_job: dict[str, float] | None, default_duration: float) -> dict[str, float]:
    duration_by_job = duration_by_job or {}
    return {name: max(float(duration_by_job.get(name, default_duration)), 0.001) for name in _job_map(workflow)}


def _validate_dependencies(jobs: dict[str, dict[str, Any]]) -> None:
    names = set(jobs)
    for name, job in jobs.items():
        missing = [dep for dep in job.get("needs", []) if dep not in names]
        if missing:
            raise ValueError(f"job {name!r} references missing needs: {missing}")


def unlimited_parallel_simulation(
    workflow: dict[str, Any],
    duration_by_job: dict[str, float] | None = None,
    *,
    default_duration: float = 1.0,
) -> dict[str, Any]:
    jobs = _job_map(workflow)
    _validate_dependencies(jobs)
    durations = _durations(workflow, duration_by_job, default_duration)
    finish: dict[str, float] = {}
    parent: dict[str, str | None] = {}
    pending = set(jobs)

    while pending:
        progressed = False
        for name in sorted(list(pending)):
            needs = list(jobs[name].get("needs", []))
            if all(dep in finish for dep in needs):
                if needs:
                    critical_parent = max(needs, key=lambda dep: finish[dep])
                    start = finish[critical_parent]
                    parent[name] = critical_parent
                else:
                    start = 0.0
                    parent[name] = None
                finish[name] = start + durations[name]
                pending.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("workflow job dependency graph contains a cycle")

    if not finish:
        return {"wall_seconds": 0.0, "total_work_seconds": 0.0, "critical_path": [], "max_theoretical_speedup": 1.0, "job_finish_seconds": {}}
    tail = max(finish, key=finish.get)
    path: list[str] = []
    current: str | None = tail
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    wall = finish[tail]
    total = sum(durations.values())
    return {
        "wall_seconds": round(wall, 6),
        "total_work_seconds": round(total, 6),
        "critical_path": path,
        "max_theoretical_speedup": round(total / wall, 6) if wall else 1.0,
        "job_finish_seconds": {name: round(value, 6) for name, value in sorted(finish.items())},
    }


def limited_worker_simulation(
    workflow: dict[str, Any],
    workers: int,
    duration_by_job: dict[str, float] | None = None,
    *,
    default_duration: float = 1.0,
) -> dict[str, Any]:
    if workers < 1:
        raise ValueError("workers must be >= 1")
    jobs = _job_map(workflow)
    _validate_dependencies(jobs)
    durations = _durations(workflow, duration_by_job, default_duration)
    completed: set[str] = set()
    scheduled: set[str] = set()
    running: list[tuple[float, str, float]] = []
    timeline: list[dict[str, Any]] = []
    now = 0.0

    while len(completed) < len(jobs):
        ready = [name for name, job in jobs.items() if name not in scheduled and set(job.get("needs", [])).issubset(completed)]
        ready.sort(key=lambda name: (-durations[name], name))
        while ready and len(running) < workers:
            name = ready.pop(0)
            scheduled.add(name)
            finish = now + durations[name]
            running.append((finish, name, now))
            timeline.append({"job": name, "start": round(now, 6), "finish": round(finish, 6)})
        if not running:
            if len(scheduled) < len(jobs):
                raise ValueError("workflow job dependency graph contains a cycle")
            break
        next_finish = min(item[0] for item in running)
        now = next_finish
        finished_now = [item for item in running if abs(item[0] - next_finish) < 1e-12]
        running = [item for item in running if abs(item[0] - next_finish) >= 1e-12]
        completed.update(item[1] for item in finished_now)

    total = sum(durations.values())
    return {
        "workers": workers,
        "wall_seconds": round(now, 6),
        "total_work_seconds": round(total, 6),
        "utilization_upper_proxy": round(total / (workers * now), 6) if now else 0.0,
        "timeline": timeline,
    }


def derive_worker_sweep(job_count: int) -> list[int]:
    if job_count <= 0:
        return [1]
    values = [1]
    workers = 2
    while workers < job_count:
        values.append(workers)
        workers *= 2
    if values[-1] != job_count:
        values.append(job_count)
    return values


def simulate_workflow(
    workflow: dict[str, Any],
    duration_by_job: dict[str, float] | None = None,
    *,
    workers: list[int] | None = None,
    default_duration: float = 1.0,
) -> dict[str, Any]:
    job_count = len(_job_map(workflow))
    sweep = workers or derive_worker_sweep(job_count)
    unlimited = unlimited_parallel_simulation(workflow, duration_by_job, default_duration=default_duration)
    limited = [limited_worker_simulation(workflow, count, duration_by_job, default_duration=default_duration) for count in sorted(set(max(1, int(value)) for value in sweep))]
    return {
        "schema": "omega-actions-digital-twin/v0.6",
        "workflow": workflow.get("path") or workflow.get("name") or "workflow",
        "job_count": job_count,
        "duration_source": "provided" if duration_by_job else "unit-default",
        "unlimited": unlimited,
        "worker_sweep": limited,
        "oak_limits": [
            "This is a scheduling twin, not a GitHub billing simulator.",
            "Unit-default durations produce structural comparisons only.",
            "Measured job durations can drift and can overlap with setup/download/upload effects.",
            "Runner availability, matrix expansion and external service contention require separate models.",
        ],
    }


def duration_map_from_telemetry(telemetry_report: dict[str, Any], *, percentile: str = "p50") -> dict[str, float]:
    result: dict[str, float] = {}
    for job in telemetry_report.get("jobs", []):
        duration = (job.get("duration_seconds") or {}).get(percentile)
        if duration is not None:
            result[str(job["name"])] = float(duration)
    return result


def render_markdown(report: dict[str, Any]) -> str:
    u = report["unlimited"]
    lines = [
        "# Ω-ACTIONS-T∞ — CI Digital Twin", "", f"- Workflow: `{report['workflow']}`",
        f"- Jobs: **{report['job_count']}**", f"- Unlimited-parallel critical wall: **{u['wall_seconds']} s**",
        f"- Total work: **{u['total_work_seconds']} s**", f"- Critical path: **{' -> '.join(u['critical_path']) or 'none'}**",
        f"- Maximum structural/theoretical speedup: **{u['max_theoretical_speedup']}×**", "", "## Worker sweep", "",
    ]
    for row in report["worker_sweep"]:
        lines.append(f"- workers={row['workers']}: wall={row['wall_seconds']} s, utilization_proxy={row['utilization_upper_proxy']}")
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in report["oak_limits"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-twin", description="Simulate a workflow DAG under worker budgets.")
    parser.add_argument("workflow_json", help="JSON file containing one workflow object from the static analyzer")
    parser.add_argument("--durations", help="Optional JSON mapping job name -> seconds")
    parser.add_argument("--workers", type=int, nargs="*")
    parser.add_argument("--default-duration", type=float, default=1.0)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)
    workflow = json.loads(Path(args.workflow_json).read_text(encoding="utf-8"))
    durations = json.loads(Path(args.durations).read_text(encoding="utf-8")) if args.durations else None
    report = simulate_workflow(workflow, durations, workers=args.workers, default_duration=args.default_duration)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        u = report["unlimited"]
        print(f"Ω-ACTIONS-T∞ twin jobs={report['job_count']} critical_wall={u['wall_seconds']}s max_speedup={u['max_theoretical_speedup']}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
