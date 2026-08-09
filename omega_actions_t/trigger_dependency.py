"""Conservative audit of whether a trigger path has an observable runtime dependency."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from omega_actions_t.trigger_hotspots import extract_positive_paths

_SUFFIXES = {".yml", ".yaml"}
_PROJECT_INSTALL_PATTERNS = (
    re.compile(r"\b(?:python\s+-m\s+pip|pip3?|uv\s+pip)\s+install\b[^\n]*(?:\s\.\s*$|\s-e\s+\.|\s--editable\s+\.)", re.MULTILINE),
    re.compile(r"\buv\s+sync\b"),
    re.compile(r"\bpoetry\s+install\b"),
    re.compile(r"\bpdm\s+install\b"),
    re.compile(r"\bpython\s+-m\s+build\b"),
)


def _job_body(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "jobs:" and len(line) - len(line.lstrip(" ")) == 0:
            return "\n".join(lines[index + 1 :])
    return ""


def audit_trigger_dependency(root: str | Path, trigger_path: str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    workflow_root = root_path / ".github" / "workflows"
    rows: list[dict[str, Any]] = []
    if workflow_root.is_dir():
        for path in sorted(workflow_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if trigger_path not in extract_positive_paths(text):
                continue
            body = _job_body(text)
            direct_reference = trigger_path in body
            install_signals = [pattern.pattern for pattern in _PROJECT_INSTALL_PATTERNS if pattern.search(body)]
            if direct_reference:
                status = "DIRECT_RUNTIME_REFERENCE"
            elif trigger_path == "pyproject.toml" and install_signals:
                status = "PROJECT_INSTALL_SIGNAL"
            else:
                status = "NO_DIRECT_RUNTIME_SIGNAL"
            rows.append({
                "workflow": path.relative_to(root_path).as_posix(),
                "trigger_path": trigger_path,
                "status": status,
                "direct_runtime_reference": direct_reference,
                "project_install_signal_count": len(install_signals),
                "migration_candidate": status == "NO_DIRECT_RUNTIME_SIGNAL",
            })
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema": "omega-actions-trigger-dependency-audit/v1",
        "trigger_path": trigger_path,
        "workflow_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "migration_candidates": [row for row in rows if row["migration_candidate"]],
        "workflows": rows,
        "oak_limits": [
            "NO_DIRECT_RUNTIME_SIGNAL is a migration candidate, not proof that the trigger path is semantically unnecessary.",
            "Transitive imports, generated metadata, packaging behavior, required checks and repository policy can create dependencies that text scanning cannot prove absent.",
            "A candidate trigger removal requires preserved validation, rollback evidence and an uncontaminated before/after protocol.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-trigger-dependency")
    parser.add_argument("--root", default=".")
    parser.add_argument("--trigger-path", default="pyproject.toml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    report = audit_trigger_dependency(args.root, args.trigger_path)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in report["workflows"]:
        print(f"{row['status']:<26} {row['workflow']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
