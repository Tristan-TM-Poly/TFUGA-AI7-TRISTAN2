from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .core import (
    REPORT_SCHEMA,
    WorkflowSpec,
    load_config,
    ordered_paths_match,
    parse_workflow,
    path_matches,
    stable_digest,
)


def _workflow_paths(root: Path) -> tuple[Path, ...]:
    workflow_root = root / ".github" / "workflows"
    paths = list(workflow_root.glob("*.yml")) + list(workflow_root.glob("*.yaml"))
    return tuple(sorted(path for path in paths if path.is_file()))


def _parse_error_spec(path: Path, root: Path, exc: Exception) -> WorkflowSpec:
    detail = " ".join(str(exc).split())
    warning = f"parse_error:{type(exc).__name__}:{detail}" if detail else f"parse_error:{type(exc).__name__}"
    return WorkflowSpec(
        path=path.relative_to(root).as_posix(),
        name=path.stem,
        events=(),
        pull_request_paths=(),
        estimated_jobs=0,
        concurrency_declared=False,
        workflow_dispatch_enabled=False,
        workflow_call_enabled=False,
        warnings=(warning,),
    )


def scan_workflows(repository_root: str | Path) -> list[WorkflowSpec]:
    """Scan every workflow without allowing one malformed file to abort observation.

    An unparseable workflow is represented as an uncertainty-bearing WorkflowSpec with
    zero estimated jobs and no inferred trigger semantics. This is deliberately conservative:
    unknown scheduler behaviour is recorded, not invented.
    """

    root = Path(repository_root)
    specs: list[WorkflowSpec] = []
    for path in _workflow_paths(root):
        try:
            specs.append(parse_workflow(path, root))
        except (OSError, RuntimeError, ValueError, Exception) as exc:  # noqa: B036 - observation boundary
            specs.append(_parse_error_spec(path, root, exc))
    return specs


def _parse_errors(specs: Iterable[WorkflowSpec]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for spec in specs:
        warnings = [item for item in spec.warnings if item.startswith("parse_error:")]
        if warnings:
            errors.append({"workflow_path": spec.path, "error": warnings[0]})
    return sorted(errors, key=lambda item: item["workflow_path"])


def _is_unparsed(spec: WorkflowSpec) -> bool:
    return any(item.startswith("parse_error:") for item in spec.warnings)


def _scope_match(path: str, patterns: tuple[str, ...]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def audit_route_config(repository_root: str | Path, config_path: str | Path) -> dict[str, Any]:
    root = Path(repository_root)
    config = load_config(config_path)
    specs = scan_workflows(root)
    scoped = [item for item in specs if _scope_match(item.path, config.legacy_scope)]
    uncovered: list[str] = []
    ambiguous: list[str] = []
    unparseable_scoped: list[str] = []
    for workflow in scoped:
        if _is_unparsed(workflow):
            unparseable_scoped.append(workflow.path)
            continue
        matches = [
            route.route_id
            for route in config.routes
            if any(path_matches(workflow.path, pattern) for pattern in route.legacy_workflow_patterns)
        ]
        if not matches:
            uncovered.append(workflow.path)
        elif len(matches) > 1:
            ambiguous.append(f"{workflow.path}:{','.join(sorted(matches))}")

    blockers: list[str] = []
    blockers.extend(f"legacy_workflow_uncovered:{item}" for item in uncovered)
    blockers.extend(f"legacy_workflow_ambiguous:{item}" for item in ambiguous)
    blockers.extend(f"legacy_workflow_unparseable:{item}" for item in unparseable_scoped)
    if not (root / config.replacement_workflow).is_file():
        blockers.append(f"replacement_workflow_missing:{config.replacement_workflow}")
    if config.replacement_green_receipt is None:
        blockers.append("replacement_green_receipt_missing")

    result = {
        "schema": "omega-ci-route-config-audit/1.1",
        "valid": not blockers,
        "legacy_workflow_count": len(scoped),
        "route_count": len(config.routes),
        "validator_count": len(config.validators),
        "uncovered_legacy_workflows": sorted(uncovered),
        "ambiguous_legacy_workflows": sorted(ambiguous),
        "unparseable_scoped_legacy_workflows": sorted(unparseable_scoped),
        "workflow_parse_errors": _parse_errors(specs),
        "replacement_green_receipt": config.replacement_green_receipt,
        "safe_to_change_legacy_triggers": False,
        "blockers": sorted(set(blockers)),
        "dry_run": True,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
        "parse_debt_is_observed_not_suppressed": True,
    }
    result["audit_digest"] = stable_digest(result)
    return result


def _hot_paths(specs: Iterable[WorkflowSpec]) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for spec in specs:
        if _is_unparsed(spec):
            continue
        for pattern in spec.pull_request_paths:
            if pattern.startswith("!"):
                continue
            row = counts.setdefault(pattern, {"pattern": pattern, "workflows": [], "estimated_jobs": 0})
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
        if spec.path == config.replacement_workflow or _is_unparsed(spec):
            continue
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
    parse_errors = _parse_errors(specs)
    report = {
        "schema": REPORT_SCHEMA,
        "observer_revision": "R0.2-resilient",
        "changed_files": list(changed),
        "scanned_workflow_count": len(specs),
        "workflow_parse_errors": parse_errors,
        "unparsed_workflow_count": len(parse_errors),
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
        "replacement_workflow_excluded_from_legacy": True,
        "legacy_estimate_excludes_unparsed_workflows": True,
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
