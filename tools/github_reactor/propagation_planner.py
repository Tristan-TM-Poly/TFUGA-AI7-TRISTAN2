#!/usr/bin/env python3
"""Generate a safe propagation plan for the Tristan GitHub Reactor.

This script reads the static repository atlas and hyperedge atlas when present,
then writes a draft-PR-oriented propagation queue. It is local-only and does not
create branches, issues, pull requests, network calls, or repository writes
outside its report directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
from dataclasses import dataclass, asdict


@dataclass
class PropagationAction:
    priority: str
    repository: str
    packet_type: str
    action: str
    reason: str
    allowed_mode: str = "additive_draft_pr_only"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_text(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_repo_blocks(text: str) -> list[dict]:
    """Tiny YAML-shape parser for the simple atlas file.

    It intentionally supports only the fields needed for the propagation report.
    This avoids adding external dependencies like PyYAML.
    """
    repos: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("  - name: "):
            if current:
                repos.append(current)
            current = {"name": line.split(": ", 1)[1].strip()}
            continue
        if current is None:
            continue
        match = re.match(r"    ([A-Za-z0-9_]+):\s*(.*)$", line)
        if match:
            key, value = match.groups()
            if value:
                current[key] = value.strip().strip("'")
    if current:
        repos.append(current)
    return repos


def make_actions(repos: list[dict]) -> list[PropagationAction]:
    actions: list[PropagationAction] = []
    for repo in repos:
        name = repo.get("name", "unknown")
        priority = repo.get("priority", "P3")
        role = repo.get("role", "unknown")
        if role == "root_reactor":
            actions.append(PropagationAction(
                priority="P0",
                repository=name,
                packet_type="root_reactor_harden",
                action="merge_or_iterate PR #36 after checking audit artifacts and M_MINUS records",
                reason="root audit spine must exist before broad propagation",
            ))
        elif role == "deep_corpus_mine":
            actions.append(PropagationAction(
                priority="P0",
                repository=name,
                packet_type="corpus_audit_adapter",
                action="add a repo-local adapter that emits reactor_oak_matrix.json from continuous_audit.py outputs",
                reason="turns the largest corpus into structured canon candidates and M_MINUS records",
            ))
        elif role == "ait_generator_package_layer":
            actions.append(PropagationAction(
                priority="P1",
                repository=name,
                packet_type="package_readiness_card",
                action="add package readiness report, pytest command, and release gate documentation",
                reason="raises the AIT generator from fertile package to reusable agent module",
            ))
        elif role == "pefa_energy_scaffold":
            actions.append(PropagationAction(
                priority="P1",
                repository=name,
                packet_type="physics_oak_contract",
                action="add assumptions, units, conservation checks, stability tests and claims.md skeleton",
                reason="converts energy theory scaffold into testable engineering package without overclaiming",
            ))
        elif role == "converted_canon_corpus":
            actions.append(PropagationAction(
                priority="P2",
                repository=name,
                packet_type="corpus_classification",
                action="classify converted documents into claim/status/reproducibility buckets",
                reason="extracts reusable canon while preserving uncertain material as fertile or M_MINUS",
            ))
        elif role == "mirror_or_variant_seed":
            actions.append(PropagationAction(
                priority="P2",
                repository=name,
                packet_type="sync_policy",
                action="define whether the repository is mirror, fork, variant, archive, or deployment seed",
                reason="prevents blind sync overwrite and clarifies propagation direction",
            ))
        else:
            actions.append(PropagationAction(
                priority=priority,
                repository=name,
                packet_type="repo_contract",
                action="add REPO_CANON_ROLE, claims, M_MINUS and audit workflow skeleton",
                reason="default reactor contract propagation",
            ))
    return actions


def score_priority(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def write_reports(out: pathlib.Path, actions: list[PropagationAction], source_files: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "source_files": source_files,
        "policy": {
            "mode": "additive_draft_pr_only",
            "blocked": ["direct_main_rewrite", "silent_promotion", "external_deploy_without_review"],
        },
        "actions": [asdict(action) for action in sorted(actions, key=lambda x: (score_priority(x.priority), x.repository))],
    }
    (out / "propagation_queue.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor Propagation Queue",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "Policy: additive draft PR only. No direct main rewrite, no silent promotion, no external deployment.",
        "",
        "## Queue",
        "",
    ]
    for action in payload["actions"]:
        lines.append(f"- **{action['priority']}** `{action['repository']}` — `{action['packet_type']}`")
        lines.append(f"  - Action: {action['action']}")
        lines.append(f"  - Reason: {action['reason']}")
    (out / "PROPAGATION_QUEUE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    repo_atlas = root / "atlas" / "github_reactor" / "repositories.yml"
    hyperedges = root / "atlas" / "github_reactor" / "hyperedges.yml"
    repos = parse_repo_blocks(read_text(repo_atlas))
    actions = make_actions(repos)
    write_reports(root / args.out, actions, {
        "repositories": str(repo_atlas.relative_to(root)) if repo_atlas.exists() else None,
        "hyperedges": str(hyperedges.relative_to(root)) if hyperedges.exists() else None,
    })
    print(json.dumps({"actions": len(actions), "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
