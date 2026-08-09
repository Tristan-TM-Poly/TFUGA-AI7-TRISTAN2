"""ΔCI / Impact Routing for Ω-ACTIONS-T∞.

This module approximates GitHub path-filter semantics without executing YAML.
It is conservative by design: workflows lacking explicit path routing remain
RUN_BROAD_UNROUTED rather than being silently skipped.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

_WORKFLOW_SUFFIXES = {".yml", ".yaml"}
_GLOBAL_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "tox.ini", "noxfile.py",
    "requirements.txt", "requirements-dev.txt", "poetry.lock", "uv.lock",
    "Pipfile", "Pipfile.lock", "package.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
}


def _strip(value: str) -> str:
    return value.strip().strip("'\"")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _glob_regex(pattern: str) -> re.Pattern[str]:
    out: list[str] = ["^"]
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        elif ch == "[":
            end = pattern.find("]", i + 1)
            if end != -1:
                out.append(pattern[i : end + 1])
                i = end
            else:
                out.append(r"\[")
        else:
            out.append(re.escape(ch))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def _pattern_matches(path: str, pattern: str) -> bool:
    return bool(_glob_regex(pattern).match(path))


def _matches_ordered(path: str, patterns: Iterable[str]) -> bool:
    matched = False
    for raw in patterns:
        raw = _strip(raw)
        if not raw:
            continue
        negated = raw.startswith("!")
        pattern = raw[1:] if negated else raw
        if _pattern_matches(path, pattern):
            matched = not negated
    return matched


def _parse_inline_trigger(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("[") and "]" in value:
        inner = value[1 : value.index("]")]
        return [_strip(item) for item in inner.split(",") if _strip(item)]
    return [_strip(value)]


def parse_workflow_filters(path: str | Path) -> dict[str, Any]:
    workflow_path = Path(path)
    lines = workflow_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    triggers: dict[str, dict[str, list[str]]] = {}
    in_on = False
    current_trigger: str | None = None
    current_filter: str | None = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ind = _indent(raw)

        if ind == 0 and (stripped.startswith("on:") or stripped.startswith("'on':") or stripped.startswith('"on":')):
            in_on = True
            current_trigger = None
            current_filter = None
            value = stripped.split(":", 1)[1].strip()
            for trigger in _parse_inline_trigger(value):
                triggers.setdefault(trigger, {"paths": [], "paths-ignore": []})
            continue

        if in_on and ind == 0:
            break
        if not in_on:
            continue

        if ind == 2 and stripped.endswith(":"):
            current_trigger = _strip(stripped[:-1])
            current_filter = None
            triggers.setdefault(current_trigger, {"paths": [], "paths-ignore": []})
            continue

        if current_trigger and ind == 4 and stripped.startswith(("paths:", "paths-ignore:")):
            key, value = stripped.split(":", 1)
            current_filter = key
            value = value.strip()
            if value.startswith("[") and "]" in value:
                inner = value[1 : value.index("]")]
                triggers[current_trigger][key].extend(_strip(item) for item in inner.split(",") if _strip(item))
            continue

        if current_trigger and current_filter and ind >= 6 and stripped.startswith("- "):
            triggers[current_trigger][current_filter].append(_strip(stripped[2:]))
            continue

        if current_trigger and ind <= 4 and current_filter:
            current_filter = None

    return {"path": workflow_path.as_posix(), "triggers": triggers}


def _event_filters(parsed: dict[str, Any], event: str) -> dict[str, list[str]] | None:
    triggers = parsed["triggers"]
    if event == "pull_request":
        for trigger in ("pull_request", "pull_request_target"):
            if trigger in triggers:
                return triggers[trigger]
        return None
    if event == "push":
        return triggers.get("push")
    return triggers.get(event)


def _workflow_files(root: Path) -> list[Path]:
    base = root / ".github" / "workflows"
    if not base.exists():
        return []
    return sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in _WORKFLOW_SUFFIXES)


def _normalize_changed(paths: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        path = str(raw).strip().replace("\\", "/")
        while path.startswith("./"):
            path = path[2:]
        if path and path not in seen:
            seen.add(path)
            normalized.append(path)
    return normalized


def classify_workflow(workflow_path: Path, root: Path, changed_files: list[str], *, event: str = "pull_request") -> dict[str, Any]:
    parsed = parse_workflow_filters(workflow_path)
    relative = workflow_path.relative_to(root).as_posix()
    filters = _event_filters(parsed, event)
    triggers = sorted(parsed["triggers"])

    if relative in changed_files:
        missing_self_filter = False
        if filters and filters.get("paths"):
            missing_self_filter = not _matches_ordered(relative, filters["paths"])
        return {
            "workflow": relative, "triggers": triggers, "decision": "RUN_WORKFLOW_SELF_CHANGE",
            "safe_skip": False, "reason": "The workflow file itself changed.",
            "paths": filters.get("paths", []) if filters else [],
            "paths_ignore": filters.get("paths-ignore", []) if filters else [],
            "matched_files": [relative], "missing_self_path_filter": missing_self_filter,
        }

    if filters is None:
        return {
            "workflow": relative, "triggers": triggers, "decision": "OUT_OF_SCOPE_EVENT",
            "safe_skip": True, "reason": f"Workflow does not declare the {event} trigger.",
            "paths": [], "paths_ignore": [], "matched_files": [], "missing_self_path_filter": False,
        }

    paths = filters.get("paths", [])
    ignored = filters.get("paths-ignore", [])
    if paths:
        matched = [path for path in changed_files if _matches_ordered(path, paths)]
        if matched:
            return {
                "workflow": relative, "triggers": triggers, "decision": "RUN_EXPLICIT_PATH_MATCH",
                "safe_skip": False, "reason": "At least one changed file matches explicit paths.",
                "paths": paths, "paths_ignore": ignored, "matched_files": matched,
                "missing_self_path_filter": False,
            }
        return {
            "workflow": relative, "triggers": triggers, "decision": "SKIP_EXPLICIT_PATH_FILTER",
            "safe_skip": True, "reason": "No changed file matches explicit paths.",
            "paths": paths, "paths_ignore": ignored, "matched_files": [], "missing_self_path_filter": False,
        }

    if ignored:
        non_ignored = [path for path in changed_files if not _matches_ordered(path, ignored)]
        if not non_ignored:
            return {
                "workflow": relative, "triggers": triggers, "decision": "SKIP_ALL_PATHS_IGNORED",
                "safe_skip": True, "reason": "Every changed file matches paths-ignore.",
                "paths": paths, "paths_ignore": ignored, "matched_files": [], "missing_self_path_filter": False,
            }
        return {
            "workflow": relative, "triggers": triggers, "decision": "RUN_PATHS_IGNORE_FALLTHROUGH",
            "safe_skip": False, "reason": "At least one changed file is not ignored.",
            "paths": paths, "paths_ignore": ignored, "matched_files": non_ignored,
            "missing_self_path_filter": False,
        }

    return {
        "workflow": relative, "triggers": triggers, "decision": "RUN_BROAD_UNROUTED",
        "safe_skip": False, "reason": f"Workflow listens to {event} without explicit path routing.",
        "paths": [], "paths_ignore": [], "matched_files": list(changed_files),
        "missing_self_path_filter": False,
    }


def plan_delta(root: str | Path, changed_files: Iterable[str], *, event: str = "pull_request") -> dict[str, Any]:
    root_path = Path(root).resolve()
    changed = _normalize_changed(changed_files)
    rows = [classify_workflow(path, root_path, changed, event=event) for path in _workflow_files(root_path)]
    by_decision: dict[str, int] = {}
    for row in rows:
        by_decision[row["decision"]] = by_decision.get(row["decision"], 0) + 1

    event_rows = [row for row in rows if row["decision"] != "OUT_OF_SCOPE_EVENT"]
    explicit = [row for row in event_rows if row["decision"] in {
        "RUN_EXPLICIT_PATH_MATCH", "SKIP_EXPLICIT_PATH_FILTER", "SKIP_ALL_PATHS_IGNORED",
        "RUN_PATHS_IGNORE_FALLTHROUGH", "RUN_WORKFLOW_SELF_CHANGE",
    }]
    broad = [row for row in event_rows if row["decision"] == "RUN_BROAD_UNROUTED"]
    safe_skips = [row for row in rows if row["safe_skip"] and row["decision"] != "OUT_OF_SCOPE_EVENT"]
    runnable = [row for row in event_rows if not row["safe_skip"]]
    missing_self = [row for row in rows if row["missing_self_path_filter"]]
    global_changed = sorted(path for path in changed if path in _GLOBAL_FILES or path.startswith(".github/actions/"))

    recommendations: list[dict[str, Any]] = []
    if broad:
        recommendations.append({
            "id": "route-broad-workflows", "priority": "high", "count": len(broad),
            "message": "Add explicit path routing or a reusable impact-gate architecture to broad PR workflows.",
            "workflows": [row["workflow"] for row in broad[:50]],
        })
    if missing_self:
        recommendations.append({
            "id": "include-workflow-self-path", "priority": "high", "count": len(missing_self),
            "message": "Path-filtered workflows should include their own workflow file when self-validation is required.",
            "workflows": [row["workflow"] for row in missing_self],
        })

    event_count = len(event_rows)
    return {
        "schema": "omega-actions-delta/v0.3", "event": event, "changed_files": changed,
        "global_impact_files": global_changed,
        "aggregate": {
            "workflow_count": len(rows), "event_workflow_count": event_count,
            "runnable_workflow_count": len(runnable), "safe_skip_count": len(safe_skips),
            "broad_unrouted_count": len(broad), "explicitly_routed_count": len(explicit),
            "routing_coverage": round(len(explicit) / event_count, 4) if event_count else 1.0,
            "provable_skip_fraction": round(len(safe_skips) / event_count, 4) if event_count else 0.0,
        },
        "decision_counts": dict(sorted(by_decision.items())), "workflows": rows,
        "recommendations": recommendations,
        "oak_limits": [
            "Broad workflows are never auto-skipped from heuristic inference.",
            "Only explicit path-filter semantics produce a provably skippable classification.",
            "Required-check and branch-protection semantics must be checked before changing trigger topology.",
            "Global dependency/build files can widen impact even when local code changes look narrow.",
            "This router approximates the common GitHub glob subset and should be regression-tested before enforcement.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Ω-ACTIONS-T∞ — ΔCI Impact Report", "", f"- Event: **{report['event']}**",
        f"- Changed files: **{len(report['changed_files'])}**", f"- Event workflows: **{a['event_workflow_count']}**",
        f"- Runnable under current explicit semantics: **{a['runnable_workflow_count']}**",
        f"- Provably skippable: **{a['safe_skip_count']}**", f"- Broad / unrouted: **{a['broad_unrouted_count']}**",
        f"- Routing coverage: **{a['routing_coverage']:.1%}**", "", "## Decisions", "",
    ]
    for key, count in sorted(report["decision_counts"].items()):
        lines.append(f"- `{key}`: **{count}**")
    lines += ["", "## Recommendations", ""]
    if report["recommendations"]:
        for item in report["recommendations"]:
            lines.append(f"- **{item['priority']} · {item['id']}** — {item['message']} ({item['count']})")
    else:
        lines.append("- No routing recommendation triggered.")
    lines += ["", "## Broad workflows", ""]
    broad = [row for row in report["workflows"] if row["decision"] == "RUN_BROAD_UNROUTED"]
    lines.extend(f"- `{row['workflow']}`" for row in broad[:100]) if broad else lines.append("- None.")
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in report["oak_limits"])
    return "\n".join(lines) + "\n"


def write_delta_report(root: str | Path, changed_files: Iterable[str], *, event: str = "pull_request", json_out: str | Path | None = None, markdown_out: str | Path | None = None) -> dict[str, Any]:
    report = plan_delta(root, changed_files, event=event)
    if json_out:
        Path(json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_out:
        Path(markdown_out).write_text(render_markdown(report), encoding="utf-8")
    return report


def _read_changed(args: argparse.Namespace) -> list[str]:
    values = list(args.changed or [])
    if args.changed_files:
        values.extend(Path(args.changed_files).read_text(encoding="utf-8").splitlines())
    return _normalize_changed(values)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-delta", description="Conservative ΔCI path-impact planner.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--event", default="pull_request", choices=("pull_request", "push"))
    parser.add_argument("--changed", action="append", help="Changed repository path; repeatable")
    parser.add_argument("--changed-files", help="Text file containing one changed path per line")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)
    changed = _read_changed(args)
    report = write_delta_report(args.root, changed, event=args.event, json_out=args.json_out, markdown_out=args.markdown_out)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        a = report["aggregate"]
        print(f"Ω-ACTIONS-T∞ delta changed={len(report['changed_files'])} event_workflows={a['event_workflow_count']} safe_skip={a['safe_skip_count']} broad_unrouted={a['broad_unrouted_count']} routing_coverage={a['routing_coverage']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
