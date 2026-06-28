#!/usr/bin/env python3
"""Build a single dashboard for GitHub Reactor artifacts.

Local-only artifact generator. It aggregates status files, validation reports,
propagation queues, Bayes-Tristan scores, inventory, and OAK matrices into one
JSON and Markdown dashboard. It does not call the network or mutate repository
source files outside the requested report directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass, asdict


@dataclass
class StatusItem:
    name: str
    value: str


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"_error": "invalid_json", "path": str(path)}


def read_status_files(out: pathlib.Path) -> list[StatusItem]:
    items: list[StatusItem] = []
    for path in sorted(out.glob("*_status.txt")):
        value = path.read_text(encoding="utf-8", errors="replace").strip()
        items.append(StatusItem(name=path.name, value=value))
    return items


def summarize_validation(report: dict) -> dict:
    if not report:
        return {"status": "missing", "errors": None, "warnings": None}
    return {
        "status": report.get("status", "unknown"),
        "errors": report.get("error_count", 0),
        "warnings": report.get("warning_count", 0),
    }


def top_ranked_actions(report: dict, limit: int = 5) -> list[dict]:
    actions = report.get("ranked_actions")
    if not isinstance(actions, list):
        return []
    return actions[:limit]


def top_queue_actions(report: dict, limit: int = 5) -> list[dict]:
    actions = report.get("actions")
    if not isinstance(actions, list):
        return []
    return actions[:limit]


def status_gate(statuses: list[StatusItem], validations: dict) -> dict:
    hard_failures = []
    soft_failures = []
    for item in statuses:
        if item.value not in {"0", "skipped", ""}:
            soft_failures.append({"name": item.name, "value": item.value})
    for name, summary in validations.items():
        if summary.get("status") == "fail":
            hard_failures.append({"name": name, "summary": summary})
    if hard_failures:
        status = "repair_required"
    elif soft_failures:
        status = "review_required"
    else:
        status = "clean_artifacts"
    return {"status": status, "hard_failures": hard_failures, "soft_failures": soft_failures}


def write_dashboard(out: pathlib.Path, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "github_reactor_dashboard.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor Dashboard",
        "",
        f"Generated: `{payload['generated_at']}`",
        f"Gate: `{payload['gate']['status']}`",
        "",
        "## Status files",
        "",
    ]
    if payload["status_files"]:
        for item in payload["status_files"]:
            lines.append(f"- `{item['name']}`: `{item['value']}`")
    else:
        lines.append("No status files found.")
    lines.extend(["", "## Validation summaries", ""])
    for name, summary in payload["validations"].items():
        lines.append(f"- `{name}`: status=`{summary['status']}`, errors=`{summary['errors']}`, warnings=`{summary['warnings']}`")
    lines.extend(["", "## Top Bayes-Tristan actions", ""])
    if payload["top_bayes_actions"]:
        for action in payload["top_bayes_actions"]:
            lines.append(f"- **{action.get('score')}** `{action.get('repository')}` — `{action.get('packet_type')}`")
            lines.append(f"  - {action.get('action')}")
    else:
        lines.append("No Bayes-Tristan scores found yet.")
    lines.extend(["", "## Top propagation queue actions", ""])
    if payload["top_queue_actions"]:
        for action in payload["top_queue_actions"]:
            lines.append(f"- `{action.get('priority')}` `{action.get('repository')}` — `{action.get('packet_type')}`")
            lines.append(f"  - {action.get('action')}")
    else:
        lines.append("No propagation queue found yet.")
    lines.extend(["", "## Gate details", ""])
    if payload["gate"]["hard_failures"]:
        lines.append("Hard failures:")
        for item in payload["gate"]["hard_failures"]:
            lines.append(f"- `{item['name']}` -> `{item['summary']['status']}`")
    if payload["gate"]["soft_failures"]:
        lines.append("Soft failures:")
        for item in payload["gate"]["soft_failures"]:
            lines.append(f"- `{item['name']}` -> `{item['value']}`")
    if not payload["gate"]["hard_failures"] and not payload["gate"]["soft_failures"]:
        lines.append("No gate failures detected from available artifacts.")
    (out / "GITHUB_REACTOR_DASHBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dashboard(out: pathlib.Path) -> dict:
    statuses = read_status_files(out)
    atlas_validation = summarize_validation(load_json(out / "atlas_validation_report.json"))
    claims_validation = summarize_validation(load_json(out / "claims_validation_report.json"))
    validations = {
        "atlas_validation": atlas_validation,
        "claims_validation": claims_validation,
    }
    bayes = load_json(out / "bayes_tristan_action_scores.json")
    queue = load_json(out / "propagation_queue.json")
    payload = {
        "generated_at": utc_now(),
        "status_files": [asdict(item) for item in statuses],
        "validations": validations,
        "top_bayes_actions": top_ranked_actions(bayes),
        "top_queue_actions": top_queue_actions(queue),
        "inventory": load_json(out / "inventory.json"),
        "reactor_oak_matrix": load_json(out / "reactor_oak_matrix.json"),
    }
    payload["gate"] = status_gate(statuses, validations)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    out = root / args.out
    payload = build_dashboard(out)
    write_dashboard(out, payload)
    print(json.dumps({"gate": payload["gate"]["status"], "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
