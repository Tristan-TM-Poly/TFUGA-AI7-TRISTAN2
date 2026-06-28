#!/usr/bin/env python3
"""GitHub Autonomous Reactor local audit kernel.

Local-only, standard-library-only audit generator.
It scans the checked-out repository and writes OAK/CVCD/Bayes-Tristan style
reports. It does not call remote APIs and does not change repository content.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import pathlib
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yml", ".yaml", ".toml", ".tex", ".csv"}

HIGH_RISK_PATTERNS = [
    r"sur[- ]?unit[eé]",
    r"[eé]nergie infinie",
    r"validation physique confirm[eé]e",
    r"supraconductivit[eé] confirm[eé]e",
    r"brevet d[eé]pos[eé]",
    r"revenu passif garanti",
]

CANONICAL_PATHS = {
    "docs": "docs",
    "tools": "tools",
    "core": "core",
    "tests": "tests",
    "schemas": "schemas",
    "claims": "claims",
    "memory": "memory",
    "github_workflows": ".github/workflows",
    "autopilot": "tools/autopilot",
    "github_reactor": "tools/github_reactor",
    "auto_genesis_reports": "reports/auto_genesis",
    "autopilot_reports": "reports/autopilot",
}

REACTOR_REPOSITORIES = [
    {"name": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", "role": "root reactor", "priority": "P0"},
    {"name": "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG", "role": "deep corpus mine", "priority": "P0"},
    {"name": "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG", "role": "AIT generator package", "priority": "P1"},
    {"name": "Tristan-TM-Poly/PEFA-FractalEnergySystem", "role": "energy research scaffold", "priority": "P1"},
    {"name": "Tristan-TM-Poly/TFACC", "role": "converted canon corpus", "priority": "P2"},
    {"name": "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2", "role": "mirror or variant seed", "priority": "P2"},
]


@dataclass
class CompileSummary:
    checked: int
    failed: int
    failures: list[dict]


@dataclass
class PatternSummary:
    files_scanned: int
    matches: int
    findings: list[dict]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def should_skip(rel: pathlib.Path) -> bool:
    return any(part in IGNORE_DIRS for part in rel.parts)


def iter_files(root: pathlib.Path, suffixes: set[str] | None = None, max_files: int = 20000) -> Iterable[pathlib.Path]:
    count = 0
    for path in root.rglob("*"):
        if count >= max_files:
            break
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if should_skip(rel):
            continue
        if suffixes is None or path.suffix.lower() in suffixes:
            count += 1
            yield path


def compile_python(root: pathlib.Path, max_files: int = 2000) -> CompileSummary:
    failures: list[dict] = []
    checked = 0
    for path in iter_files(root, {".py"}, max_files=max_files):
        checked += 1
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except Exception as exc:
            failures.append({"path": str(path.relative_to(root)), "error": repr(exc)[:500]})
    return CompileSummary(checked=checked, failed=len(failures), failures=failures[:100])


def pattern_scan(root: pathlib.Path, max_files: int = 5000) -> PatternSummary:
    compiled = [(raw, re.compile(raw, re.IGNORECASE)) for raw in HIGH_RISK_PATTERNS]
    findings: list[dict] = []
    files_scanned = 0
    matches = 0
    for path in iter_files(root, TEXT_SUFFIXES, max_files=max_files):
        files_scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw, pat in compiled:
            for match in pat.finditer(text):
                matches += 1
                line = text.count("\n", 0, match.start()) + 1
                findings.append({"path": str(path.relative_to(root)), "line": line, "pattern": raw})
                if len(findings) >= 200:
                    return PatternSummary(files_scanned=files_scanned, matches=matches, findings=findings)
    return PatternSummary(files_scanned=files_scanned, matches=matches, findings=findings)


def inventory(root: pathlib.Path) -> dict:
    suffixes: Counter[str] = Counter()
    top_dirs: Counter[str] = Counter()
    total = 0
    for path in iter_files(root, None):
        total += 1
        rel = path.relative_to(root)
        suffixes[path.suffix.lower() or "[no_suffix]"] += 1
        if rel.parts:
            top_dirs[rel.parts[0]] += 1
    return {
        "file_count": total,
        "suffix_counts": suffixes.most_common(40),
        "top_dirs": top_dirs.most_common(40),
        "canonical_paths": {name: (root / rel).exists() for name, rel in CANONICAL_PATHS.items()},
        "package_manifests": {
            "pyproject": (root / "pyproject.toml").exists(),
            "requirements": (root / "requirements.txt").exists(),
            "package_json": (root / "package.json").exists(),
            "makefile": (root / "Makefile").exists(),
            "dockerfile": (root / "Dockerfile").exists(),
        },
    }


def oak_score(inv: dict, comp: CompileSummary, patterns: PatternSummary) -> dict:
    paths = inv["canonical_paths"]
    score = 0
    components = {}
    checks = {
        "docs": paths.get("docs", False),
        "workflows": paths.get("github_workflows", False),
        "tools": paths.get("tools", False),
        "core_or_prototypes": paths.get("core", False),
        "schemas_or_claims": paths.get("schemas", False) or paths.get("claims", False),
        "memory": paths.get("memory", False),
        "autopilot_or_reactor": paths.get("autopilot", False) or paths.get("github_reactor", False),
    }
    for key, ok in checks.items():
        components[key] = 10 if ok else 0
        score += components[key]
    components["python_compile"] = 20 if comp.checked > 0 and comp.failed == 0 else 10 if comp.checked == 0 else 0
    components["claim_hygiene_scan"] = 10 if patterns.matches == 0 else 5 if patterns.matches <= 5 else 0
    score += components["python_compile"] + components["claim_hygiene_scan"]
    if score >= 80:
        status = "CANON_READY_SOFTWARE_SCAFFOLD"
    elif score >= 60:
        status = "FERTILE_NEEDS_REPAIR"
    elif score >= 40:
        status = "OAK_TEST_REQUIRED"
    else:
        status = "M_MINUS_REPAIR_REQUIRED"
    return {"score": min(score, 100), "max_score": 100, "status": status, "components": components}


def next_actions(score: dict, comp: CompileSummary, patterns: PatternSummary, inv: dict) -> list[dict]:
    actions: list[dict] = []
    paths = inv["canonical_paths"]
    if comp.failed > 0:
        actions.append({"priority": "P0", "action": "repair_python_compile_failures", "reason": "direct OAK blocker"})
    if patterns.matches > 0:
        actions.append({"priority": "P0", "action": "review_high_risk_claims", "reason": "reduces overclaim risk"})
    if not paths.get("tests", False):
        actions.append({"priority": "P1", "action": "add_minimal_tests_directory", "reason": "raises testability"})
    if not paths.get("schemas", False):
        actions.append({"priority": "P1", "action": "add_schema_contracts", "reason": "turns claims into machine-checkable objects"})
    if not paths.get("memory", False):
        actions.append({"priority": "P1", "action": "add_m_minus_registry", "reason": "stores failed patterns as negative memory"})
    actions.append({"priority": "P2", "action": "propagate_repo_contract_by_draft_pr", "reason": "maximizes HGFM coherence with review gates"})
    return actions


def write_reports(out: pathlib.Path, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "reactor_oak_matrix.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor OAK Matrix",
        "",
        f"Generated: `{payload['generated_at']}`",
        f"Repository: `{payload['repository']}`",
        "",
        "## OAK score",
        "",
        f"- Score: **{payload['oak_score']['score']} / {payload['oak_score']['max_score']}**",
        f"- Status: `{payload['oak_score']['status']}`",
        "",
        "## Components",
        "",
    ]
    for key, value in payload["oak_score"]["components"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Next actions", ""])
    for action in payload["next_actions"]:
        lines.append(f"- **{action['priority']}** — `{action['action']}`: {action['reason']}")
    lines.extend(["", "## Interrepo reactor targets", ""])
    for repo in payload["reactor_repositories"]:
        lines.append(f"- **{repo['priority']}** `{repo['name']}` — {repo['role']}")
    lines.extend(["", "## Guardrail", "", "This report is an audit artifact only. It is not proof, deployment, or permission to merge automatically."])
    (out / "REACTOR_OAK_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    inv = inventory(root)
    comp = compile_python(root)
    patterns = pattern_scan(root)
    score = oak_score(inv, comp, patterns)
    payload = {
        "generated_at": utc_now(),
        "repository": os.environ.get("GITHUB_REPOSITORY", root.name),
        "ref": os.environ.get("GITHUB_REF_NAME"),
        "sha": os.environ.get("GITHUB_SHA"),
        "inventory": inv,
        "python_compile": asdict(comp),
        "claim_hygiene_scan": asdict(patterns),
        "oak_score": score,
        "next_actions": next_actions(score, comp, patterns, inv),
        "reactor_repositories": REACTOR_REPOSITORIES,
        "blocked_behaviors": ["direct_main_rewrite", "auto_merge_without_review", "external_deploy_without_policy", "claim_certification_without_evidence"],
    }
    out = root / args.out
    write_reports(out, payload)
    print(json.dumps({"repository": payload["repository"], "score": score["score"], "status": score["status"], "out": str(out.relative_to(root))}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
