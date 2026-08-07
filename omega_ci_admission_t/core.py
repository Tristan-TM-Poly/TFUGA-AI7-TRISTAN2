from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

CONFIG_SCHEMA = "omega-ci-route-config/1"
REPORT_SCHEMA = "omega-ci-admission-report/1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _nonempty(value: Any, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{field_name} must be non-empty")
    return result


def _strings(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(_nonempty(item, field_name) for item in value)
    if not allow_empty and not result:
        raise ValueError(f"{field_name} cannot be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return result


def path_matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    pattern = pattern.replace("\\", "/").lstrip("./")
    return fnmatch.fnmatchcase(path, pattern)


def ordered_paths_match(path: str, patterns: Iterable[str]) -> bool:
    matched = False
    positive = False
    for raw in patterns:
        negated = raw.startswith("!")
        pattern = raw[1:] if negated else raw
        if not negated:
            positive = True
        if path_matches(path, pattern):
            matched = not negated
    return matched if positive else False


@dataclass(frozen=True)
class WorkflowSpec:
    path: str
    name: str
    events: tuple[str, ...]
    pull_request_paths: tuple[str, ...]
    estimated_jobs: int
    concurrency_declared: bool
    workflow_dispatch_enabled: bool
    workflow_call_enabled: bool
    warnings: tuple[str, ...]

    def pr_match(self, changed_files: Iterable[str]) -> tuple[bool, tuple[str, ...]]:
        if "pull_request" not in self.events:
            return False, ()
        if not self.pull_request_paths:
            return True, ("unfiltered_pull_request_trigger",)
        matches = tuple(
            path
            for path in changed_files
            if ordered_paths_match(path, self.pull_request_paths)
        )
        return bool(matches), matches

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_path": self.path,
            "name": self.name,
            "events": list(self.events),
            "pull_request_paths": list(self.pull_request_paths),
            "estimated_jobs": self.estimated_jobs,
            "concurrency_declared": self.concurrency_declared,
            "workflow_dispatch_enabled": self.workflow_dispatch_enabled,
            "workflow_call_enabled": self.workflow_call_enabled,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class Route:
    route_id: str
    owned_paths: tuple[str, ...]
    suite_args: tuple[str, ...]
    legacy_workflow_patterns: tuple[str, ...]
    estimated_jobs: int

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "Route":
        allowed = {
            "route_id",
            "owned_paths",
            "suite_args",
            "legacy_workflow_patterns",
            "estimated_jobs",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown route fields: {sorted(unknown)}")
        estimated = row.get("estimated_jobs")
        if not isinstance(estimated, int) or isinstance(estimated, bool) or estimated < 1:
            raise ValueError("estimated_jobs must be positive")
        return cls(
            route_id=_nonempty(row.get("route_id"), "route_id"),
            owned_paths=_strings(row.get("owned_paths", []), "owned_paths"),
            suite_args=_strings(row.get("suite_args", []), "suite_args"),
            legacy_workflow_patterns=_strings(
                row.get("legacy_workflow_patterns", []), "legacy_workflow_patterns"
            ),
            estimated_jobs=estimated,
        )

    def matches(self, changed_file: str) -> bool:
        return any(path_matches(changed_file, pattern) for pattern in self.owned_paths)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "owned_paths": list(self.owned_paths),
            "suite_args": list(self.suite_args),
            "legacy_workflow_patterns": list(self.legacy_workflow_patterns),
            "estimated_jobs": self.estimated_jobs,
        }


@dataclass(frozen=True)
class Validator:
    validator_id: str
    paths: tuple[str, ...]
    command_args: tuple[str, ...]
    estimated_jobs: int

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "Validator":
        allowed = {"validator_id", "paths", "command_args", "estimated_jobs"}
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown validator fields: {sorted(unknown)}")
        estimated = row.get("estimated_jobs")
        if not isinstance(estimated, int) or isinstance(estimated, bool) or estimated < 1:
            raise ValueError("validator estimated_jobs must be positive")
        return cls(
            validator_id=_nonempty(row.get("validator_id"), "validator_id"),
            paths=_strings(row.get("paths", []), "validator paths"),
            command_args=_strings(row.get("command_args", []), "command_args"),
            estimated_jobs=estimated,
        )

    def matches(self, changed_file: str) -> bool:
        return any(path_matches(changed_file, pattern) for pattern in self.paths)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "paths": list(self.paths),
            "command_args": list(self.command_args),
            "estimated_jobs": self.estimated_jobs,
        }


@dataclass(frozen=True)
class RouteConfig:
    replacement_workflow: str
    legacy_scope: tuple[str, ...]
    routes: tuple[Route, ...]
    validators: tuple[Validator, ...]
    replacement_green_receipt: str | None

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RouteConfig":
        allowed = {
            "schema",
            "replacement_workflow",
            "legacy_scope",
            "routes",
            "validators",
            "replacement_green_receipt",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown config fields: {sorted(unknown)}")
        if row.get("schema") != CONFIG_SCHEMA:
            raise ValueError(f"schema must equal {CONFIG_SCHEMA}")
        route_rows = row.get("routes")
        validator_rows = row.get("validators")
        if not isinstance(route_rows, list) or not isinstance(validator_rows, list):
            raise ValueError("routes and validators must be lists")
        routes = tuple(Route.from_dict(item) for item in route_rows)
        validators = tuple(Validator.from_dict(item) for item in validator_rows)
        route_ids = [item.route_id for item in routes]
        validator_ids = [item.validator_id for item in validators]
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("duplicate route IDs")
        if len(validator_ids) != len(set(validator_ids)):
            raise ValueError("duplicate validator IDs")
        receipt = row.get("replacement_green_receipt")
        if receipt is not None:
            receipt = _nonempty(receipt, "replacement_green_receipt")
        return cls(
            replacement_workflow=_nonempty(
                row.get("replacement_workflow"), "replacement_workflow"
            ),
            legacy_scope=_strings(row.get("legacy_scope", []), "legacy_scope"),
            routes=routes,
            validators=validators,
            replacement_green_receipt=receipt,
        )


def load_config(path: str | Path) -> RouteConfig:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("route config root must be an object")
    return RouteConfig.from_dict(value)


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for workflow scanning") from exc
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


def _paths(event: Any) -> tuple[str, ...]:
    if not isinstance(event, Mapping):
        return ()
    result: list[str] = []
    include = event.get("paths")
    exclude = event.get("paths-ignore")
    if isinstance(include, list):
        result.extend(str(item) for item in include)
    if isinstance(exclude, list):
        result.extend("!" + str(item).lstrip("!") for item in exclude)
    return tuple(result)


def _job_expansion(job: Any) -> tuple[int, tuple[str, ...]]:
    if not isinstance(job, Mapping):
        return 1, ()
    strategy = job.get("strategy")
    if not isinstance(strategy, Mapping):
        return 1, ()
    matrix = strategy.get("matrix")
    if not isinstance(matrix, Mapping):
        return 1, ()
    product = 1
    include = 0
    exclude = 0
    warnings: list[str] = []
    for key, value in matrix.items():
        key = str(key)
        if key == "include":
            include = len(value) if isinstance(value, list) else 0
        elif key == "exclude":
            exclude = len(value) if isinstance(value, list) else 0
        elif isinstance(value, list):
            product *= max(1, len(value))
        else:
            warnings.append(f"dynamic_matrix_axis:{key}")
    return max(1, product - exclude) + include, tuple(warnings)


def parse_workflow(path: Path, root: Path) -> WorkflowSpec:
    raw = _load_yaml(path)
    events = _event_map(raw.get("on"))
    jobs = raw.get("jobs", {})
    estimated = 0
    warnings: list[str] = []
    if isinstance(jobs, Mapping):
        for job_id, job in jobs.items():
            expansion, job_warnings = _job_expansion(job)
            estimated += expansion
            warnings.extend(f"{job_id}:{warning}" for warning in job_warnings)
    else:
        warnings.append("jobs_not_object")
    return WorkflowSpec(
        path=path.relative_to(root).as_posix(),
        name=str(raw.get("name") or path.stem),
        events=tuple(sorted(events)),
        pull_request_paths=_paths(events.get("pull_request")),
        estimated_jobs=max(1, estimated),
        concurrency_declared="concurrency" in raw,
        workflow_dispatch_enabled="workflow_dispatch" in events,
        workflow_call_enabled="workflow_call" in events,
        warnings=tuple(sorted(set(warnings))),
    )


def scan_workflows(repository_root: str | Path) -> list[WorkflowSpec]:
    root = Path(repository_root)
    paths = sorted((root / ".github" / "workflows").glob("*.yml"))
    paths += sorted((root / ".github" / "workflows").glob("*.yaml"))
    return [parse_workflow(path, root) for path in paths if path.is_file()]


def _scope_match(path: str, patterns: tuple[str, ...]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def audit_route_config(repository_root: str | Path, config_path: str | Path) -> dict[str, Any]:
    root = Path(repository_root)
    config = load_config(config_path)
    specs = scan_workflows(root)
    scoped = [item for item in specs if _scope_match(item.path, config.legacy_scope)]
    uncovered: list[str] = []
    ambiguous: list[str] = []
    for workflow in scoped:
        matches = [
            route.route_id
            for route in config.routes
            if any(
                path_matches(workflow.path, pattern)
                for pattern in route.legacy_workflow_patterns
            )
        ]
        if not matches:
            uncovered.append(workflow.path)
        elif len(matches) > 1:
            ambiguous.append(f"{workflow.path}:{','.join(sorted(matches))}")
    blockers: list[str] = []
    blockers.extend(f"legacy_workflow_uncovered:{item}" for item in uncovered)
    blockers.extend(f"legacy_workflow_ambiguous:{item}" for item in ambiguous)
    if not (root / config.replacement_workflow).is_file():
        blockers.append(f"replacement_workflow_missing:{config.replacement_workflow}")
    if config.replacement_green_receipt is None:
        blockers.append("replacement_green_receipt_missing")
    result = {
        "schema": "omega-ci-route-config-audit/1",
        "valid": not blockers,
        "legacy_workflow_count": len(scoped),
        "route_count": len(config.routes),
        "validator_count": len(config.validators),
        "uncovered_legacy_workflows": sorted(uncovered),
        "ambiguous_legacy_workflows": sorted(ambiguous),
        "replacement_green_receipt": config.replacement_green_receipt,
        "safe_to_change_legacy_triggers": False,
        "blockers": sorted(set(blockers)),
        "dry_run": True,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
    }
    result["audit_digest"] = stable_digest(result)
    return result


def _hot_paths(specs: Iterable[WorkflowSpec]) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for spec in specs:
        for pattern in spec.pull_request_paths:
            if pattern.startswith("!"):
                continue
            row = counts.setdefault(
                pattern,
                {"pattern": pattern, "workflows": [], "estimated_jobs": 0},
            )
            row["workflows"].append(spec.path)
            row["estimated_jobs"] += spec.estimated_jobs
    return sorted(
        (
            {
                **row,
                "workflow_count": len(row["workflows"]),
                "workflows": sorted(row["workflows"]),
            }
            for row in counts.values()
        ),
        key=lambda row: (-row["workflow_count"], -row["estimated_jobs"], row["pattern"]),
    )


def build_admission_report(
    repository_root: str | Path,
    config_path: str | Path,
    changed_files: Iterable[str],
) -> dict[str, Any]:
    root = Path(repository_root)
    config = load_config(config_path)
    specs = scan_workflows(root)
    changed = tuple(
        sorted(
            {
                str(path).replace("\\", "/").lstrip("./")
                for path in changed_files
                if str(path).strip()
            }
        )
    )
    legacy: list[dict[str, Any]] = []
    for spec in specs:
        eligible, matches = spec.pr_match(changed)
        if eligible:
            legacy.append(
                {
                    "workflow_path": spec.path,
                    "name": spec.name,
                    "matched_paths": list(matches),
                    "estimated_jobs": spec.estimated_jobs,
                    "unfiltered": matches == ("unfiltered_pull_request_trigger",),
                }
            )
    routes: list[dict[str, Any]] = []
    for route in config.routes:
        matches = sorted(path for path in changed if route.matches(path))
        if matches:
            routes.append(
                {
                    "route_id": route.route_id,
                    "matched_paths": matches,
                    "suite_args": list(route.suite_args),
                    "estimated_jobs": route.estimated_jobs,
                }
            )
    validators: list[dict[str, Any]] = []
    for validator in config.validators:
        matches = sorted(path for path in changed if validator.matches(path))
        if matches:
            validators.append(
                {
                    "validator_id": validator.validator_id,
                    "matched_paths": matches,
                    "command_args": list(validator.command_args),
                    "estimated_jobs": validator.estimated_jobs,
                }
            )
    legacy_jobs = sum(item["estimated_jobs"] for item in legacy)
    replacement_jobs = sum(item["estimated_jobs"] for item in routes + validators)
    reduction = legacy_jobs - replacement_jobs
    audit = audit_route_config(root, config_path)
    report = {
        "schema": REPORT_SCHEMA,
        "changed_files": list(changed),
        "scanned_workflow_count": len(specs),
        "legacy_triggered_workflows": sorted(legacy, key=lambda item: item["workflow_path"]),
        "estimated_legacy_jobs": legacy_jobs,
        "selected_routes": sorted(routes, key=lambda item: item["route_id"]),
        "selected_validators": sorted(validators, key=lambda item: item["validator_id"]),
        "estimated_replacement_jobs": replacement_jobs,
        "estimated_job_reduction": reduction,
        "estimated_job_reduction_ratio": reduction / legacy_jobs if legacy_jobs else 0.0,
        "hot_paths": _hot_paths(specs)[:50],
        "route_config_audit_digest": audit["audit_digest"],
        "route_config_valid": audit["valid"],
        "replacement_green_receipt_present": config.replacement_green_receipt is not None,
        "safe_to_change_legacy_triggers": False,
        "dry_run": True,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
        "workflow_dispatch_performed": False,
        "path_matching_is_approximate": True,
        "estimate_is_not_github_scheduler_truth": True,
    }
    report["report_digest"] = stable_digest(report)
    return report
