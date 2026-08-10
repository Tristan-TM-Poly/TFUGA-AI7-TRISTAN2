"""Detect shared GitHub Actions trigger paths that amplify repository fan-out."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_SUFFIXES = {".yml", ".yaml"}


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def extract_positive_paths(text: str) -> list[str]:
    """Extract list entries under trigger-level ``paths:`` blocks.

    The scanner intentionally stops at ``jobs:`` so step-level keys cannot be
    mistaken for event filters. It is a conservative structural parser, not a
    general YAML implementation.
    """
    lines = text.splitlines()
    result: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "jobs:" and _indent(line) == 0:
            break
        if stripped != "paths:":
            continue
        base = _indent(line)
        cursor = index + 1
        while cursor < len(lines):
            child = lines[cursor]
            if not child.strip():
                cursor += 1
                continue
            if _indent(child) <= base:
                break
            item = child.strip()
            if item.startswith("-"):
                value = item[1:].strip().strip("'\"")
                if value:
                    result.append(value)
            cursor += 1
    return result


def analyze_trigger_hotspots(root: str | Path) -> dict:
    root_path = Path(root)
    workflow_root = root_path / ".github" / "workflows"
    occurrences: dict[str, set[str]] = defaultdict(set)
    workflow_count = 0

    if workflow_root.is_dir():
        for path in sorted(workflow_root.rglob("*")):
            if path.suffix.lower() not in _SUFFIXES or not path.is_file():
                continue
            workflow_count += 1
            relative = str(path.relative_to(root_path))
            text = path.read_text(encoding="utf-8", errors="replace")
            for trigger_path in set(extract_positive_paths(text)):
                occurrences[trigger_path].add(relative)

    hotspots = [
        {
            "path": trigger_path,
            "workflow_count": len(workflows),
            "workflows": sorted(workflows),
            "fanout_score": len(workflows),
        }
        for trigger_path, workflows in occurrences.items()
    ]
    hotspots.sort(key=lambda item: (-item["workflow_count"], item["path"]))

    return {
        "schema": "omega-actions-trigger-hotspots/v1",
        "workflow_count": workflow_count,
        "unique_trigger_paths": len(occurrences),
        "hotspots": hotspots,
        "shared_hotspots": [item for item in hotspots if item["workflow_count"] >= 2],
        "oak_limits": [
            "Frequency is a fan-out signal, not proof that a trigger is unnecessary.",
            "Required-check and dependency semantics must be reviewed before removing a shared trigger.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-trigger-hotspots")
    parser.add_argument("--root", default=".")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    report = analyze_trigger_hotspots(args.root)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    for item in report["hotspots"][: max(0, args.top)]:
        print(f"{item['workflow_count']:>4}  {item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
