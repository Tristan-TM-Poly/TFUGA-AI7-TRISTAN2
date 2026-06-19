#!/usr/bin/env python3
"""Validate GitHub Reactor atlas files without external dependencies.

This is intentionally a small local-only validator. It checks the repository
atlas and hyperedge atlas for required fields, duplicates, and basic enum
constraints, then writes JSON and Markdown validation reports.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
from dataclasses import dataclass, asdict

REQUIRED_REPO_FIELDS = {
    "name",
    "role",
    "priority",
    "visibility",
    "oak_status",
}

ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_VISIBILITIES = {"public", "private", "internal", "unknown"}
ALLOWED_OAK_STATUS = {"CANON", "FERTILE", "OAK_TEST", "REPAIR", "M_MINUS", "ARCHIVE"}

REQUIRED_HYPEREDGE_FIELDS = {
    "id",
    "label",
    "transformation",
    "oak_gate",
    "cvcd_gain",
    "risk",
}


@dataclass
class ValidationFinding:
    severity: str
    file: str
    item: str
    message: str


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_text(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_blocks(text: str, marker: str) -> list[dict]:
    blocks: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith(f"  - {marker}: "):
            if current:
                blocks.append(current)
            current = {marker: line.split(": ", 1)[1].strip().strip("'")}
            continue
        if current is None:
            continue
        match = re.match(r"    ([A-Za-z0-9_]+):\s*(.*)$", line)
        if match:
            key, value = match.groups()
            if value:
                current[key] = value.strip().strip("'")
    if current:
        blocks.append(current)
    return blocks


def validate_repositories(path: pathlib.Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    text = read_text(path)
    if not text:
        return [ValidationFinding("error", str(path), "file", "repository atlas missing or empty")]
    repos = parse_blocks(text, "name")
    if not repos:
        findings.append(ValidationFinding("error", str(path), "repositories", "no repository blocks found"))
        return findings
    seen: set[str] = set()
    for repo in repos:
        name = repo.get("name", "<missing>")
        missing = sorted(REQUIRED_REPO_FIELDS - set(repo))
        if missing:
            findings.append(ValidationFinding("error", str(path), name, f"missing fields: {', '.join(missing)}"))
        if name in seen:
            findings.append(ValidationFinding("error", str(path), name, "duplicate repository name"))
        seen.add(name)
        if "/" not in name:
            findings.append(ValidationFinding("error", str(path), name, "repository name should be owner/repo"))
        if repo.get("priority") and repo["priority"] not in ALLOWED_PRIORITIES:
            findings.append(ValidationFinding("error", str(path), name, f"invalid priority: {repo['priority']}"))
        if repo.get("visibility") and repo["visibility"] not in ALLOWED_VISIBILITIES:
            findings.append(ValidationFinding("error", str(path), name, f"invalid visibility: {repo['visibility']}"))
        if repo.get("oak_status") and repo["oak_status"] not in ALLOWED_OAK_STATUS:
            findings.append(ValidationFinding("error", str(path), name, f"invalid oak_status: {repo['oak_status']}"))
    return findings


def validate_hyperedges(path: pathlib.Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    text = read_text(path)
    if not text:
        return [ValidationFinding("error", str(path), "file", "hyperedge atlas missing or empty")]
    edges = parse_blocks(text, "id")
    if not edges:
        findings.append(ValidationFinding("error", str(path), "hyperedges", "no hyperedge blocks found"))
        return findings
    seen: set[str] = set()
    for edge in edges:
        edge_id = edge.get("id", "<missing>")
        missing = sorted(REQUIRED_HYPEREDGE_FIELDS - set(edge))
        if missing:
            findings.append(ValidationFinding("error", str(path), edge_id, f"missing fields: {', '.join(missing)}"))
        if edge_id in seen:
            findings.append(ValidationFinding("error", str(path), edge_id, "duplicate hyperedge id"))
        seen.add(edge_id)
    return findings


def write_reports(out: pathlib.Path, findings: list[ValidationFinding]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "status": "pass" if not findings else "fail",
        "error_count": sum(1 for item in findings if item.severity == "error"),
        "warning_count": sum(1 for item in findings if item.severity == "warning"),
        "findings": [asdict(item) for item in findings],
    }
    (out / "atlas_validation_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor Atlas Validation",
        "",
        f"Generated: `{payload['generated_at']}`",
        f"Status: `{payload['status']}`",
        f"Errors: `{payload['error_count']}`",
        f"Warnings: `{payload['warning_count']}`",
        "",
    ]
    if findings:
        lines.append("## Findings")
        lines.append("")
        for finding in findings:
            lines.append(f"- **{finding.severity}** `{finding.file}` / `{finding.item}` — {finding.message}")
    else:
        lines.append("No validation findings.")
    (out / "ATLAS_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    repo_atlas = root / "atlas" / "github_reactor" / "repositories.yml"
    hyperedges = root / "atlas" / "github_reactor" / "hyperedges.yml"
    findings = []
    findings.extend(validate_repositories(repo_atlas))
    findings.extend(validate_hyperedges(hyperedges))
    write_reports(root / args.out, findings)
    print(json.dumps({"status": "pass" if not findings else "fail", "findings": len(findings), "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
