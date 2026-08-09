"""OAK gate for measuring GitHub Actions path-filter migrations on pull requests.

A pull-request workflow is selected from the cumulative PR diff, not merely the
latest commit. This module prevents a latest-commit witness from being treated
as causal evidence when older PR changes still match a workflow's trigger.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from omega_actions_t.delta_ci import (
    _event_filters,
    _matches_ordered,
    _normalize_changed,
    _workflow_files,
    parse_workflow_filters,
)


def _matching(paths: Iterable[str], patterns: Iterable[str]) -> list[str]:
    patterns_list = list(patterns)
    return [path for path in paths if _matches_ordered(path, patterns_list)]


def assess_workflow_measurement(
    workflow_path: str | Path,
    root: str | Path,
    commit_changed_paths: Iterable[str],
    pull_request_changed_paths: Iterable[str],
    *,
    event: str = "pull_request",
) -> dict[str, Any]:
    """Assess whether a workflow run can be attributed to the latest commit.

    ``commit_changed_paths`` is the latest commit delta. For ``pull_request``
    events, ``pull_request_changed_paths`` must be the cumulative base..head PR
    file set. A matching path that exists only in the cumulative PR set is a
    carry-over confounder.
    """
    root_path = Path(root).resolve()
    path = Path(workflow_path)
    if not path.is_absolute():
        path = root_path / path
    relative = path.relative_to(root_path).as_posix()
    parsed = parse_workflow_filters(path)
    filters = _event_filters(parsed, event)
    commit_changed = _normalize_changed(commit_changed_paths)
    pr_changed = _normalize_changed(pull_request_changed_paths)

    if filters is None:
        return {
            "workflow": relative,
            "event": event,
            "status": "OUT_OF_SCOPE_EVENT",
            "eligible_under_pr_diff": False,
            "measurement_valid": True,
            "commit_matches": [],
            "pr_matches": [],
            "carryover_matches": [],
            "self_changed_in_pr": relative in pr_changed,
            "reason": f"Workflow does not declare the {event} trigger.",
        }

    paths = filters.get("paths", [])
    ignored = filters.get("paths-ignore", [])
    if not paths:
        return {
            "workflow": relative,
            "event": event,
            "status": "BROAD_OR_NEGATIVE_FILTER_ONLY",
            "eligible_under_pr_diff": True,
            "measurement_valid": False,
            "commit_matches": [],
            "pr_matches": [],
            "carryover_matches": [],
            "self_changed_in_pr": relative in pr_changed,
            "reason": "No positive paths filter exists; latest-commit path attribution is not sufficient.",
            "paths_ignore": ignored,
        }

    commit_matches = _matching(commit_changed, paths)
    pr_matches = _matching(pr_changed, paths)
    commit_set = set(commit_changed)
    carryover_matches = [path for path in pr_matches if path not in commit_set]
    eligible = bool(pr_matches)
    self_changed = relative in pr_changed

    if not eligible:
        status = "NOT_ELIGIBLE_UNDER_PR_DIFF"
        valid = True
        reason = "No cumulative pull-request path matches the workflow's positive paths filter."
    elif carryover_matches and commit_matches:
        status = "MIXED_PR_DIFF_CONTAMINATION"
        valid = False
        reason = "Latest-commit matches coexist with older cumulative PR matches, so the run cause is not isolated."
    elif carryover_matches:
        status = "PR_DIFF_CARRYOVER_CONTAMINATED"
        valid = False
        reason = "The workflow is eligible only because an older cumulative PR change still matches its paths filter."
    elif commit_matches:
        status = "ATTRIBUTABLE_TO_LATEST_COMMIT"
        valid = True
        reason = "Every matching cumulative PR path is present in the latest commit delta."
    else:
        status = "INCONSISTENT_DIFF_INPUT"
        valid = False
        reason = "Workflow eligibility could not be reconciled between commit and cumulative PR path sets."

    return {
        "workflow": relative,
        "event": event,
        "status": status,
        "eligible_under_pr_diff": eligible,
        "measurement_valid": valid,
        "commit_matches": commit_matches,
        "pr_matches": pr_matches,
        "carryover_matches": carryover_matches,
        "self_changed_in_pr": self_changed,
        "paths": paths,
        "paths_ignore": ignored,
        "reason": reason,
    }


def assess_repository_measurement(
    root: str | Path,
    commit_changed_paths: Iterable[str],
    pull_request_changed_paths: Iterable[str],
    *,
    event: str = "pull_request",
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    rows = [
        assess_workflow_measurement(path, root_path, commit_changed_paths, pull_request_changed_paths, event=event)
        for path in _workflow_files(root_path)
    ]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    contaminated = [row for row in rows if not row["measurement_valid"]]
    attributable = [row for row in rows if row["status"] == "ATTRIBUTABLE_TO_LATEST_COMMIT"]
    return {
        "schema": "omega-actions-pr-diff-semantics/v1",
        "event": event,
        "commit_changed_paths": _normalize_changed(commit_changed_paths),
        "pull_request_changed_paths": _normalize_changed(pull_request_changed_paths),
        "status_counts": dict(sorted(counts.items())),
        "aggregate": {
            "workflow_count": len(rows),
            "attributable_count": len(attributable),
            "contaminated_or_non_attributable_count": len(contaminated),
            "measurement_protocol_clean": not contaminated,
        },
        "workflows": rows,
        "oak_limits": [
            "For pull_request, use the cumulative base..head PR file set when reproducing path-filter eligibility.",
            "A workflow changed earlier in the same PR can remain self-eligible even when the latest commit does not touch it.",
            "A same-PR latest-commit witness cannot prove trigger narrowing when carry-over matches remain.",
            "Use a fresh post-merge PR, an isolated branch without workflow self-changes, or another uncontaminated protocol for causal before/after proof.",
        ],
    }


def _read_lines(path: str | None) -> list[str]:
    if not path:
        return []
    return Path(path).read_text(encoding="utf-8").splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-pr-diff-gate")
    parser.add_argument("--root", default=".")
    parser.add_argument("--event", default="pull_request", choices=("pull_request", "push"))
    parser.add_argument("--commit-changed-files", required=True)
    parser.add_argument("--pr-changed-files", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    report = assess_repository_measurement(
        args.root,
        _read_lines(args.commit_changed_files),
        _read_lines(args.pr_changed_files),
        event=args.event,
    )
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["aggregate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
