from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .model import (
    REPORT_SCHEMA,
    RouteConfig,
    WorkflowSpec,
    github_pattern_matches,
    load_route_config,
    stable_digest,
)
from .scanner import scan_workflows, workflow_hot_paths


def scan_repository_workflows(repository_root: str | Path) -> list[dict[str, Any]]:
    return [item.to_dict() for item in scan_workflows(repository_root)]


def _legacy_in_scope(spec: WorkflowSpec, config: RouteConfig) -> bool:
    return any(
        github_pattern_matches(spec.workflow_path, pattern)
        for pattern in config.legacy_scope
    )


def _covered_legacy_paths(config: RouteConfig) -> set[str]:
    return {
        pattern
        for route in config.routes
        for pattern in route.legacy_workflow_patterns
    }


def audit_route_config(
    repository_root: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    config = load_route_config(config_path)
    specs = scan_workflows(repository_root)
    scoped = [item for item in specs if _legacy_in_scope(item, config)]
    uncovered: list[str] = []
    ambiguous: list[str] = []
    for spec in scoped:
        matching_routes = [
            route.route_id
            for route in config.routes
            if any(
                github_pattern_matches(spec.workflow_path, pattern)
                for pattern in route.legacy_workflow_patterns
            )
        ]
        if not matching_routes:
            uncovered.append(spec.workflow_path)
        elif len(matching_routes) > 1:
            ambiguous.append(f"{spec.workflow_path}:{','.join(sorted(matching_routes))}")

    missing_replacements = sorted(
        {
            route.replacement_workflow
            for route in config.routes
            if not (Path(repository_root) / route.replacement_workflow).is_file()
        }
    )
    blockers = []
    blockers.extend(f"legacy_workflow_uncovered:{item}" for item in uncovered)
    blockers.extend(f"legacy_workflow_ambiguous:{item}" for item in ambiguous)
    blockers.extend(f"replacement_workflow_missing:{item}" for item in missing_replacements)
    if config.replacement_green_receipt is None:
        blockers.append("replacement_green_receipt_missing")

    result = {
        "schema": "omega-ci-route-config-audit/1",
        "valid": not blockers,
        "legacy_workflow_count": len(scoped),
        "route_count": len(config.routes),
        "shared_validator_count": len(config.shared_validators),
        "uncovered_legacy_workflows": sorted(uncovered),
        "ambiguous_legacy_workflows": sorted(ambiguous),
        "missing_replacement_workflows": missing_replacements,
        "replacement_green_receipt": config.replacement_green_receipt,
        "safe_to_change_legacy_triggers": False,
        "blockers": sorted(set(blockers)),
        "dry_run": True,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
    }
    result["audit_digest"] = stable_digest(result)
    return result


def _selected_routes(config: RouteConfig, changed_files: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in config.routes:
        owned_matches = sorted(
            path for path in changed_files if route.owned_match(path)
        )
        if not owned_matches:
            continue
        shared_matches = sorted(
            path for path in changed_files if route.shared_match(path)
        )
        row = {
            "route_id": route.route_id,
            "owned_matches": owned_matches,
            "shared_matches": shared_matches,
            "suite_command": route.suite_command,
            "replacement_workflow": route.replacement_workflow,
            "estimated_jobs": route.estimated_jobs,
        }
        row["route_digest"] = stable_digest(row)
        rows.append(row)
    return sorted(rows, key=lambda item: item["route_id"])


def _selected_validators(config: RouteConfig, changed_files: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for validator in config.shared_validators:
        matches = sorted(path for path in changed_files if validator.matches(path))
        if not matches:
            continue
        row = {
            "validator_id": validator.validator_id,
            "matches": matches,
            "suite_command": validator.suite_command,
            "estimated_jobs": validator.estimated_jobs,
        }
        row["validator_digest"] = stable_digest(row)
        rows.append(row)
    return sorted(rows, key=lambda item: item["validator_id"])


def build_admission_report(
    repository_root: str | Path,
    config_path: str | Path,
    changed_files: Iterable[str],
) -> dict[str, Any]:
    root = Path(repository_root)
    config = load_route_config(config_path)
    specs = scan_workflows(root)
    changed = tuple(sorted({str(path).replace("\\", "/").lstrip("./") for path in changed_files if str(path).strip()}))

    legacy_triggered: list[dict[str, Any]] = []
    for spec in specs:
        eligible, matches = spec.pull_request_eligible(changed)
        if not eligible:
            continue
        legacy_triggered.append(
            {
                "workflow_path": spec.workflow_path,
                "name": spec.name,
                "matched_paths": list(matches),
                "estimated_jobs": spec.estimated_matrix_jobs,
                "unfiltered": matches == ("unfiltered_pull_request_trigger",),
            }
        )

    routes = _selected_routes(config, changed)
    validators = _selected_validators(config, changed)
    routed_jobs = sum(item["estimated_jobs"] for item in routes)
    validator_jobs = sum(item["estimated_jobs"] for item in validators)
    legacy_jobs = sum(item["estimated_jobs"] for item in legacy_triggered)
    replacement_jobs = routed_jobs + validator_jobs
    reduction = legacy_jobs - replacement_jobs
    reduction_ratio = reduction / legacy_jobs if legacy_jobs else 0.0

    config_audit = audit_route_config(root, config_path)
    report = {
        "schema": REPORT_SCHEMA,
        "changed_files": list(changed),
        "changed_file_count": len(changed),
        "scanned_workflow_count": len(specs),
        "legacy_triggered_workflows": sorted(
            legacy_triggered,
            key=lambda item: item["workflow_path"],
        ),
        "legacy_triggered_workflow_count": len(legacy_triggered),
        "estimated_legacy_jobs": legacy_jobs,
        "selected_routes": routes,
        "selected_shared_validators": validators,
        "estimated_replacement_jobs": replacement_jobs,
        "estimated_job_reduction": reduction,
        "estimated_job_reduction_ratio": reduction_ratio,
        "workflow_hot_paths": workflow_hot_paths(specs)[:50],
        "route_config_audit_digest": config_audit["audit_digest"],
        "route_config_valid": config_audit["valid"],
        "safe_to_change_legacy_triggers": False,
        "replacement_green_receipt_present": config.replacement_green_receipt is not None,
        "dry_run": True,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
        "workflow_dispatch_performed": False,
        "estimate_is_not_github_scheduler_truth": True,
        "path_matching_is_approximate": True,
    }
    report["report_digest"] = stable_digest(report)
    return report
