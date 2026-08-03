from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import WorkflowSpec


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to scan workflow files") from exc
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, Mapping):
        raise ValueError(f"workflow root must be an object: {path}")
    return value


def _event_map(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {value: {}}
    if isinstance(value, list):
        return {str(item): {} for item in value}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _paths_for(event_config: Any) -> tuple[str, ...]:
    if not isinstance(event_config, Mapping):
        return ()
    paths = event_config.get("paths")
    paths_ignore = event_config.get("paths-ignore")
    result: list[str] = []
    if isinstance(paths, list):
        result.extend(str(item) for item in paths)
    if isinstance(paths_ignore, list):
        result.extend("!" + str(item).lstrip("!") for item in paths_ignore)
    return tuple(result)


def _matrix_expansion(job: Any) -> tuple[int, list[str]]:
    warnings: list[str] = []
    if not isinstance(job, Mapping):
        return 1, warnings
    strategy = job.get("strategy")
    if not isinstance(strategy, Mapping):
        return 1, warnings
    matrix = strategy.get("matrix")
    if not isinstance(matrix, Mapping):
        return 1, warnings
    product = 1
    include_count = 0
    exclude_count = 0
    for key, value in matrix.items():
        key = str(key)
        if key == "include":
            include_count = len(value) if isinstance(value, list) else 0
            continue
        if key == "exclude":
            exclude_count = len(value) if isinstance(value, list) else 0
            continue
        if isinstance(value, list):
            product *= max(1, len(value))
        else:
            warnings.append(f"dynamic_matrix_axis:{key}")
    estimate = max(1, product - exclude_count) + include_count
    return estimate, warnings


def parse_workflow(path: str | Path, *, repository_root: str | Path | None = None) -> WorkflowSpec:
    workflow_path = Path(path)
    root = Path(repository_root) if repository_root is not None else workflow_path.parents[2]
    relative = workflow_path.relative_to(root).as_posix()
    raw = _load_yaml(workflow_path)
    events = _event_map(raw.get("on"))
    jobs = raw.get("jobs", {})
    warnings: list[str] = []
    job_definitions = len(jobs) if isinstance(jobs, Mapping) else 0
    estimated_jobs = 0
    if isinstance(jobs, Mapping):
        for job_id, job in jobs.items():
            expansion, job_warnings = _matrix_expansion(job)
            estimated_jobs += expansion
            warnings.extend(f"{job_id}:{item}" for item in job_warnings)
    else:
        warnings.append("jobs_not_object")
    if estimated_jobs == 0:
        estimated_jobs = 1
    return WorkflowSpec(
        workflow_path=relative,
        name=str(raw.get("name") or workflow_path.stem),
        events=tuple(sorted(events)),
        pull_request_paths=_paths_for(events.get("pull_request")),
        push_paths=_paths_for(events.get("push")),
        job_definitions=job_definitions,
        estimated_matrix_jobs=estimated_jobs,
        concurrency_declared="concurrency" in raw,
        workflow_call_enabled="workflow_call" in events,
        workflow_dispatch_enabled="workflow_dispatch" in events,
        parse_warnings=tuple(sorted(set(warnings))),
    )


def scan_workflows(
    repository_root: str | Path,
    *,
    workflow_glob: str = ".github/workflows/*.*ml",
) -> list[WorkflowSpec]:
    root = Path(repository_root)
    specs = [
        parse_workflow(path, repository_root=root)
        for path in sorted(root.glob(workflow_glob))
        if path.is_file()
    ]
    return sorted(specs, key=lambda item: item.workflow_path)


def workflow_hot_paths(specs: Iterable[WorkflowSpec]) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for spec in specs:
        for pattern in spec.pull_request_paths:
            if pattern.startswith("!"):
                continue
            row = counts.setdefault(
                pattern,
                {"pattern": pattern, "workflow_paths": [], "estimated_jobs": 0},
            )
            row["workflow_paths"].append(spec.workflow_path)
            row["estimated_jobs"] += spec.estimated_matrix_jobs
    return sorted(
        (
            {
                **row,
                "workflow_count": len(row["workflow_paths"]),
                "workflow_paths": sorted(row["workflow_paths"]),
            }
            for row in counts.values()
        ),
        key=lambda row: (-row["workflow_count"], -row["estimated_jobs"], row["pattern"]),
    )
