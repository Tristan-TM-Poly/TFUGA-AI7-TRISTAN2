#!/usr/bin/env python3
"""Generate reviewable issue drafts from Bayes-Tristan action scores.

Local-only artifact generator. It reads ranked actions and writes issue draft
objects that a human can later review, edit, and open manually or through a
separate explicit command. It does not call GitHub APIs, create issues, create
branches, or mutate source files outside the report directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass, asdict


@dataclass
class IssueDraft:
    rank: int
    repository: str
    title: str
    labels: list[str]
    body: str
    source_score: float
    allowed_mode: str = "draft_only"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def label_for_packet(packet_type: str) -> list[str]:
    labels = ["github-reactor", "oak-review"]
    if packet_type.startswith("root"):
        labels.append("root-reactor")
    if "physics" in packet_type:
        labels.append("physics-oak")
    if "package" in packet_type:
        labels.append("package-readiness")
    if "corpus" in packet_type:
        labels.append("corpus-canon")
    if "sync" in packet_type:
        labels.append("sync-policy")
    return labels


def make_title(action: dict) -> str:
    priority = action.get("priority", "P3")
    packet = action.get("packet_type", "repo_contract")
    repo = action.get("repository", "unknown")
    return f"[{priority}] {packet}: {repo}"


def make_body(action: dict) -> str:
    return "\n".join([
        "## GitHub Reactor issue draft",
        "",
        f"Repository: `{action.get('repository', 'unknown')}`",
        f"Priority: `{action.get('priority', 'P3')}`",
        f"Packet type: `{action.get('packet_type', 'repo_contract')}`",
        f"Bayes-Tristan score: `{action.get('score', 'n/a')}`",
        "",
        "## Proposed action",
        "",
        str(action.get("action", "")),
        "",
        "## Reason",
        "",
        str(action.get("reason", "")),
        "",
        "## Score components",
        "",
        f"- information_gain: `{action.get('information_gain', 'n/a')}`",
        f"- cvcd_gain: `{action.get('cvcd_gain', 'n/a')}`",
        f"- prototype_value: `{action.get('prototype_value', 'n/a')}`",
        f"- cost: `{action.get('cost', 'n/a')}`",
        f"- risk: `{action.get('risk', 'n/a')}`",
        f"- m_minus_penalty: `{action.get('m_minus_penalty', 'n/a')}`",
        "",
        "## OAK boundary",
        "",
        "This is a generated draft, not an automatically opened issue. Review before creating any GitHub issue or PR.",
    ])


def generate_drafts(scores: dict, limit: int) -> list[IssueDraft]:
    ranked = scores.get("ranked_actions")
    if not isinstance(ranked, list):
        return []
    drafts: list[IssueDraft] = []
    for raw in ranked[:limit]:
        if not isinstance(raw, dict):
            continue
        packet = str(raw.get("packet_type", "repo_contract"))
        drafts.append(IssueDraft(
            rank=int(raw.get("rank", len(drafts) + 1) or len(drafts) + 1),
            repository=str(raw.get("repository", "unknown")),
            title=make_title(raw),
            labels=label_for_packet(packet),
            body=make_body(raw),
            source_score=float(raw.get("score", 0.0) or 0.0),
        ))
    return drafts


def write_reports(out: pathlib.Path, drafts: list[IssueDraft]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "policy": "draft_only_no_github_api_calls",
        "draft_count": len(drafts),
        "drafts": [asdict(item) for item in drafts],
    }
    (out / "issue_drafts.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor Issue Drafts",
        "",
        f"Generated: `{payload['generated_at']}`",
        f"Policy: `{payload['policy']}`",
        "",
    ]
    if drafts:
        for draft in payload["drafts"]:
            lines.append(f"## {draft['rank']}. {draft['title']}")
            lines.append("")
            lines.append(f"Repository: `{draft['repository']}`")
            lines.append(f"Labels: `{', '.join(draft['labels'])}`")
            lines.append(f"Score: `{draft['source_score']}`")
            lines.append("")
            lines.append(draft["body"])
            lines.append("")
    else:
        lines.append("No issue drafts generated because no Bayes-Tristan ranked actions were found.")
    (out / "ISSUE_DRAFTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    out = root / args.out
    scores = load_json(out / "bayes_tristan_action_scores.json")
    drafts = generate_drafts(scores, limit=max(0, args.limit))
    write_reports(out, drafts)
    print(json.dumps({"issue_drafts": len(drafts), "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
