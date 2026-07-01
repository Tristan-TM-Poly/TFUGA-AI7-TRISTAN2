"""Generate local Ω-AUTO²-OAK-FIXALL-T batch reports.

This script is side-effect free: it reads local decision JSON files and writes
local report files only when requested. It does not call GitHub or mutate repos.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from validate_decision import validate_decision


DECISIONS = [
    "MERGE_NOW",
    "REPAIR_SAFE",
    "WAIT_COOLDOWN",
    "BLOCK_M_MINUS",
    "HUMAN_APPROVAL_REQUIRED",
]


def load_decision(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_path"] = str(path)
    data["_errors"] = validate_decision(data)
    return data


def summarize(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(item.get("decision", "INVALID") for item in decisions)
    blocker_counts: Counter[str] = Counter()
    by_repo: dict[str, Counter[str]] = defaultdict(Counter)
    invalid_files = []

    for item in decisions:
        decision = item.get("decision", "INVALID")
        repo = item.get("repo", "unknown")
        by_repo[repo][decision] += 1
        for blocker in item.get("blockers", []) or []:
            blocker_counts[str(blocker)] += 1
        if item.get("_errors"):
            invalid_files.append({"path": item.get("_path"), "errors": item.get("_errors")})

    return {
        "total_items": len(decisions),
        "decision_counts": dict(sorted(decision_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "by_repo": {repo: dict(counter) for repo, counter in sorted(by_repo.items())},
        "invalid_files": invalid_files,
    }


def render_markdown(summary: dict[str, Any], decisions: list[dict[str, Any]]) -> str:
    lines = [
        "# Ω-AUTO²-OAK-FIXALL-T Batch Report",
        "",
        "This report is generated from local decision JSON files. It is a dry-run artifact and performs no external actions.",
        "",
        f"Total items: {summary['total_items']}",
        "",
        "## Decision counts",
        "",
    ]

    for decision in DECISIONS:
        lines.append(f"- {decision}: {summary['decision_counts'].get(decision, 0)}")
    for decision, count in summary["decision_counts"].items():
        if decision not in DECISIONS:
            lines.append(f"- {decision}: {count}")

    lines.extend(["", "## Blocker counts", ""])
    if summary["blocker_counts"]:
        for blocker, count in summary["blocker_counts"].items():
            lines.append(f"- {blocker}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Items", ""])
    for item in decisions:
        blockers = ", ".join(item.get("blockers", []) or []) or "none"
        errors = "; ".join(item.get("_errors", []) or []) or "none"
        lines.append(
            f"- `{item.get('repo', 'unknown')}` item `{item.get('item_id', 'unknown')}`: "
            f"{item.get('decision', 'INVALID')} | blockers: {blockers} | validation_errors: {errors}"
        )

    lines.extend(["", "## OAK rule", "", "Do not merge from this report alone. Merge still requires live PR verification and head SHA locking.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a dry-run FixAll batch report.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()

    decisions = [load_decision(path) for path in args.paths]
    summary = summarize(decisions)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(summary, decisions), encoding="utf-8")

    if not args.json_out and not args.md_out:
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 1 if summary["invalid_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
