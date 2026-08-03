from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

REPORT_SCHEMA = "omega-ci-admission-report/1"
CONFIG_SCHEMA = "omega-ci-route-config/1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require_nonempty(value: Any, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{field_name} must be non-empty")
    return result


def require_string_list(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(require_nonempty(item, field_name) for item in value)
    if not allow_empty and not result:
        raise ValueError(f"{field_name} cannot be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return result


def github_pattern_matches(path: str, pattern: str) -> bool:
    """Approximate GitHub path-filter matching for deterministic dry-run analysis."""
    normalized_path = path.replace("\\", "/").lstrip("./")
    normalized_pattern = pattern.replace("\\", "/").lstrip("./")
    return fnmatch.fnmatchcase(normalized_path, normalized_pattern)


def ordered_filter_match(path: str, patterns: Iterable[str]) -> bool:
    matched = False
    saw_positive = False
    for raw_pattern in patterns:
        negated = raw_pattern.startswith("!")
        pattern = raw_pattern[1:] if negated else raw_pattern
        if not negated:
            saw_positive = True
        if github_pattern_matches(path, pattern):
            matched = not negated
    return matched if saw_positive else False


@dataclass(frozen=True)
class WorkflowSpec:
    workflow_path: str
    name: str
    events: tuple[str, ...]
    pull_request_paths: tuple[str, ...]
    push_paths: tuple[str, ...]
    job_definitions: int
    estimated_matrix_jobs: int
    concurrency_declared: bool
    workflow_call_enabled: bool
    workflow_dispatch_enabled: bool
    parse_warnings: tuple[str, ...] = field(default_factory=tuple)

    def pull_request_eligible(self, changed_files: Iterable[str]) -> tuple[bool, tuple[str, ...]]:
        files = tuple(changed_files)
        if "pull_request" not in self.events:
            return False, ()
        if not self.pull_request_paths:
            return True, ("unfiltered_pull_request_trigger",)
        matched = tuple(
            path for path in files if ordered_filter_match(path, self.pull_request_paths)
        )
        return bool(matched), matched

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_path": self.workflow_path,
            "name": self.name,
            "events": list(self.events),
            "pull_request_paths": list(self.pull_request_paths),
            "push_paths": list(self.push_paths),
            "job_definitions": self.job_definitions,
            "estimated_matrix_jobs": self.estimated_matrix_jobs,
            "concurrency_declared": self.concurrency_declared,
            "workflow_call_enabled": self.workflow_call_enabled,
            "workflow_dispatch_enabled": self.workflow_dispatch_enabled,
            "parse_warnings": list(self.parse_warnings),
        }


@dataclass(frozen=True)
class RouteSpec:
    route_id: str
    owned_paths: tuple[str, ...]
    shared_paths: tuple[str, ...]
    suite_command: str
    replacement_workflow: str
    legacy_workflow_patterns: tuple[str, ...]
    estimated_jobs: int

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RouteSpec":
        allowed = {
            "route_id",
            "owned_paths",
            "shared_paths",
            "suite_command",
            "replacement_workflow",
            "legacy_workflow_patterns",
            "estimated_jobs",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown route fields: {sorted(unknown)}")
        estimated_jobs = row.get("estimated_jobs")
        if not isinstance(estimated_jobs, int) or isinstance(estimated_jobs, bool) or estimated_jobs < 1:
            raise ValueError("estimated_jobs must be a positive integer")
        return cls(
            route_id=require_nonempty(row.get("route_id"), "route_id"),
            owned_paths=require_string_list(row.get("owned_paths", []), "owned_paths"),
            shared_paths=require_string_list(
                row.get("shared_paths", []), "shared_paths", allow_empty=True
            ),
            suite_command=require_nonempty(row.get("suite_command"), "suite_command"),
            replacement_workflow=require_nonempty(
                row.get("replacement_workflow"), "replacement_workflow"
            ),
            legacy_workflow_patterns=require_string_list(
                row.get("legacy_workflow_patterns", []),
                "legacy_workflow_patterns",
            ),
            estimated_jobs=estimated_jobs,
        )

    def owned_match(self, changed_file: str) -> bool:
        return any(github_pattern_matches(changed_file, pattern) for pattern in self.owned_paths)

    def shared_match(self, changed_file: str) -> bool:
        return any(github_pattern_matches(changed_file, pattern) for pattern in self.shared_paths)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "owned_paths": list(self.owned_paths),
            "shared_paths": list(self.shared_paths),
            "suite_command": self.suite_command,
            "replacement_workflow": self.replacement_workflow,
            "legacy_workflow_patterns": list(self.legacy_workflow_patterns),
            "estimated_jobs": self.estimated_jobs,
        }


@dataclass(frozen=True)
class SharedValidator:
    validator_id: str
    paths: tuple[str, ...]
    suite_command: str
    estimated_jobs: int

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "SharedValidator":
        allowed = {"validator_id", "paths", "suite_command", "estimated_jobs"}
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown validator fields: {sorted(unknown)}")
        estimated_jobs = row.get("estimated_jobs")
        if not isinstance(estimated_jobs, int) or isinstance(estimated_jobs, bool) or estimated_jobs < 1:
            raise ValueError("validator estimated_jobs must be positive")
        return cls(
            validator_id=require_nonempty(row.get("validator_id"), "validator_id"),
            paths=require_string_list(row.get("paths", []), "validator paths"),
            suite_command=require_nonempty(row.get("suite_command"), "validator suite_command"),
            estimated_jobs=estimated_jobs,
        )

    def matches(self, changed_file: str) -> bool:
        return any(github_pattern_matches(changed_file, pattern) for pattern in self.paths)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "paths": list(self.paths),
            "suite_command": self.suite_command,
            "estimated_jobs": self.estimated_jobs,
        }


@dataclass(frozen=True)
class RouteConfig:
    routes: tuple[RouteSpec, ...]
    shared_validators: tuple[SharedValidator, ...]
    legacy_scope: tuple[str, ...]
    replacement_green_receipt: str | None

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RouteConfig":
        allowed = {
            "schema",
            "routes",
            "shared_validators",
            "legacy_scope",
            "replacement_green_receipt",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown config fields: {sorted(unknown)}")
        if row.get("schema") != CONFIG_SCHEMA:
            raise ValueError(f"schema must equal {CONFIG_SCHEMA}")
        route_rows = row.get("routes")
        validator_rows = row.get("shared_validators")
        if not isinstance(route_rows, list) or not isinstance(validator_rows, list):
            raise ValueError("routes and shared_validators must be lists")
        routes = tuple(RouteSpec.from_dict(item) for item in route_rows)
        validators = tuple(SharedValidator.from_dict(item) for item in validator_rows)
        route_ids = [item.route_id for item in routes]
        validator_ids = [item.validator_id for item in validators]
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("route IDs must be unique")
        if len(validator_ids) != len(set(validator_ids)):
            raise ValueError("validator IDs must be unique")
        receipt = row.get("replacement_green_receipt")
        if receipt is not None:
            receipt = require_nonempty(receipt, "replacement_green_receipt")
        return cls(
            routes=routes,
            shared_validators=validators,
            legacy_scope=require_string_list(row.get("legacy_scope", []), "legacy_scope"),
            replacement_green_receipt=receipt,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CONFIG_SCHEMA,
            "routes": [item.to_dict() for item in self.routes],
            "shared_validators": [item.to_dict() for item in self.shared_validators],
            "legacy_scope": list(self.legacy_scope),
            "replacement_green_receipt": self.replacement_green_receipt,
        }


def load_route_config(path: str | Path) -> RouteConfig:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("route config root must be an object")
    return RouteConfig.from_dict(value)
