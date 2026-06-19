#!/usr/bin/env python3
"""Bayes-Tristan action scorer for the GitHub Reactor.

Local-only artifact generator. It reads the propagation queue, claims registry,
validation reports, and M_MINUS seed memory when present. It writes a ranked
Bayes-Tristan action matrix without creating issues, branches, pull requests,
network calls, or external side effects.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass, asdict

PRIORITY_BONUS = {"P0": 35.0, "P1": 24.0, "P2": 14.0, "P3": 6.0}
PACKET_VALUE = {
    "root_reactor_harden": 28.0,
    "corpus_audit_adapter": 26.0,
    "physics_oak_contract": 25.0,
    "package_readiness_card": 20.0,
    "corpus_classification": 16.0,
    "sync_policy": 12.0,
    "repo_contract": 14.0,
}
RISK_PENALTY = {
    "root_reactor_harden": 7.0,
    "corpus_audit_adapter": 9.0,
    "physics_oak_contract": 13.0,
    "package_readiness_card": 6.0,
    "corpus_classification": 7.0,
    "sync_policy": 4.0,
    "repo_contract": 5.0,
}


@dataclass
class RankedAction:
    rank: int
    repository: str
    priority: str
    packet_type: str
    action: str
    reason: str
    information_gain: float
    cvcd_gain: float
    prototype_value: float
    cost: float
    risk: float
    m_minus_penalty: float
    score: float


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def load_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def normalize_actions(queue: dict) -> list[dict]:
    actions = queue.get("actions")
    if isinstance(actions, list):
        return [item for item in actions if isinstance(item, dict)]
    return []


def validation_penalty(report: dict) -> float:
    if not report:
        return 5.0
    errors = float(report.get("error_count", 0) or 0)
    warnings = float(report.get("warning_count", 0) or 0)
    return errors * 20.0 + warnings * 5.0


def repo_claim_bonus(repository: str, claims: list[dict]) -> float:
    bonus = 0.0
    for claim in claims:
        text = " ".join(str(claim.get(key, "")) for key in ("claim", "domain", "next_test"))
        if repository.split("/", 1)[-1] in text or repository in text:
            status = claim.get("oak_status")
            if status == "CANON":
                bonus += 8.0
            elif status == "FERTILE":
                bonus += 5.0
            elif status == "OAK_TEST":
                bonus += 6.0
            elif status in {"REPAIR", "M_MINUS"}:
                bonus += 3.0
    return min(bonus, 18.0)


def repo_mminus_penalty(repository: str, memories: list[dict]) -> float:
    penalty = 0.0
    for item in memories:
        repo = str(item.get("repository", ""))
        if repo == "ALL" or repo == repository:
            status = str(item.get("status", ""))
            if "PENDING" in status:
                penalty += 8.0
            elif "ACTIVE" in status:
                penalty += 5.0
            else:
                penalty += 2.0
    return min(penalty, 22.0)


def score_actions(actions: list[dict], claims: list[dict], memories: list[dict], report_penalty: float) -> list[RankedAction]:
    ranked: list[RankedAction] = []
    for action in actions:
        repository = str(action.get("repository", "unknown"))
        priority = str(action.get("priority", "P3"))
        packet_type = str(action.get("packet_type", "repo_contract"))
        info = PRIORITY_BONUS.get(priority, 0.0) + repo_claim_bonus(repository, claims)
        cvcd = PACKET_VALUE.get(packet_type, 10.0)
        prototype = 18.0 if packet_type in {"root_reactor_harden", "corpus_audit_adapter", "package_readiness_card", "physics_oak_contract"} else 10.0
        cost = {"P0": 12.0, "P1": 10.0, "P2": 7.0, "P3": 4.0}.get(priority, 6.0)
        risk = RISK_PENALTY.get(packet_type, 6.0)
        mminus = repo_mminus_penalty(repository, memories) + report_penalty
        score = info + cvcd + prototype - cost - risk - mminus
        ranked.append(RankedAction(
            rank=0,
            repository=repository,
            priority=priority,
            packet_type=packet_type,
            action=str(action.get("action", "")),
            reason=str(action.get("reason", "")),
            information_gain=round(info, 2),
            cvcd_gain=round(cvcd, 2),
            prototype_value=round(prototype, 2),
            cost=round(cost, 2),
            risk=round(risk, 2),
            m_minus_penalty=round(mminus, 2),
            score=round(score, 2),
        ))
    ranked.sort(key=lambda item: item.score, reverse=True)
    for index, item in enumerate(ranked, start=1):
        item.rank = index
    return ranked


def write_reports(out: pathlib.Path, ranked: list[RankedAction], sources: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "formula": "score = information_gain + cvcd_gain + prototype_value - cost - risk - m_minus_penalty",
        "sources": sources,
        "ranked_actions": [asdict(item) for item in ranked],
    }
    (out / "bayes_tristan_action_scores.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Bayes-Tristan Action Scores",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "Formula:",
        "",
        "```text",
        payload["formula"],
        "```",
        "",
        "## Ranked actions",
        "",
    ]
    for item in payload["ranked_actions"]:
        lines.append(f"{item['rank']}. **{item['score']}** `{item['repository']}` — `{item['packet_type']}`")
        lines.append(f"   - Priority: `{item['priority']}`")
        lines.append(f"   - Action: {item['action']}")
        lines.append(f"   - Reason: {item['reason']}")
        lines.append(f"   - Components: info={item['information_gain']}, cvcd={item['cvcd_gain']}, prototype={item['prototype_value']}, cost={item['cost']}, risk={item['risk']}, m_minus={item['m_minus_penalty']}")
    (out / "BAYES_TRISTAN_ACTION_SCORES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    out = root / args.out
    queue_path = out / "propagation_queue.json"
    claims_path = root / "claims" / "github_reactor_claims.jsonl"
    memory_path = root / "memory" / "m_minus" / "github_reactor_m_minus_seed.jsonl"
    atlas_report = out / "atlas_validation_report.json"
    claims_report = out / "claims_validation_report.json"
    queue = load_json(queue_path)
    claims = load_jsonl(claims_path)
    memories = load_jsonl(memory_path)
    report_penalty = validation_penalty(load_json(atlas_report)) + validation_penalty(load_json(claims_report))
    ranked = score_actions(normalize_actions(queue), claims, memories, report_penalty)
    write_reports(out, ranked, {
        "propagation_queue": str(queue_path.relative_to(root)) if queue_path.exists() else None,
        "claims": str(claims_path.relative_to(root)) if claims_path.exists() else None,
        "m_minus": str(memory_path.relative_to(root)) if memory_path.exists() else None,
        "atlas_validation": str(atlas_report.relative_to(root)) if atlas_report.exists() else None,
        "claims_validation": str(claims_report.relative_to(root)) if claims_report.exists() else None,
    })
    print(json.dumps({"ranked_actions": len(ranked), "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
