"""AIT-PANTHEON-OMEGA 16-circ-n engine.

Dependency-free prototype engine for generating role/mode AIT candidates,
attacking them with simple OAK heuristics, selecting top16, burying bottom16 in
negative memory, and decompressing the best candidate into a one-page codex.

This is an architectural tool, not an autonomous external agent.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROLES: Sequence[str] = (
    "Trace Extractor",
    "Canon Compiler",
    "OAK Attacker",
    "Math Formalizer",
    "Physics Residual Finder",
    "Code Builder",
    "Test Generator",
    "Prototype Forge",
    "Data Scout",
    "Literature Scout",
    "HGFM Mapper",
    "Memory Curator",
    "Negative Memory Guardian",
    "Codex Generator",
    "Strategy Optimizer",
    "GitHub Operator",
)

MODES: Sequence[str] = (
    "fast",
    "deep",
    "skeptical",
    "creative",
    "mathematical",
    "experimental",
    "software",
    "business",
    "pedagogical",
    "compression",
    "decompression",
    "adversarial",
    "benchmark",
    "safety",
    "synthesis",
    "meta_generation",
)


@dataclass(frozen=True)
class AITCandidate:
    id: str
    role: str
    mode: str
    mission: str
    cycle: int
    fertility: float
    oak_score: float
    reuse: float
    prototype_value: float
    impact: float
    transmission: float
    cost: float
    risk: float
    hype: float
    complexity: float
    debt: float
    score: float
    status: str
    attacks: List[str]
    next_action: str


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _unit(seed: str, field: str) -> float:
    return (_hash_int(f"{seed}|{field}") % 1000) / 999


def _oak_attacks(role: str, mode: str, oak_score: float, hype: float, prototype_value: float) -> List[str]:
    attacks = []
    if oak_score < 0.65:
        attacks.append("OAK below promotion threshold; keep as candidate or quarantine.")
    if hype > 4.5:
        attacks.append("AntiHype warning: reduce claims or add tests before decompression.")
    if prototype_value < 4.0:
        attacks.append("Prototype path weak; generate a minimal test before promotion.")
    if mode in {"creative", "meta_generation"} and oak_score < 0.75:
        attacks.append("Creative/meta mode requires stronger adversarial verification.")
    if role == "GitHub Operator":
        attacks.append("External writes must stay restricted to repository artifacts and explicit user intent.")
    if not attacks:
        attacks.append("No blocking attack found; decompress into codex/test/prototype.")
    return attacks


def build_candidate(role: str, mode: str, mission: str, cycle: int, salt: str = "") -> AITCandidate:
    seed = f"{salt}|{mission}|{cycle}|{role}|{mode}"
    fertility = 10 * (0.40 * _unit(seed, "fertility") + 0.30 * _unit(seed, "bridge") + 0.30 * _unit(seed, "descendants"))
    oak_score = min(1.0, 0.35 * _unit(seed, "trace") + 0.35 * _unit(seed, "attack") + 0.30 * _unit(seed, "anti_hype"))
    reuse = 10 * (0.40 * _unit(seed, "reuse") + 0.30 * _unit(seed, "compression") + 0.30 * _unit(seed, "transmission"))
    prototype_value = 10 * (0.45 * _unit(seed, "prototype") + 0.30 * _unit(seed, "test") + 0.25 * _unit(seed, "measurement"))
    impact = 10 * (0.40 * _unit(seed, "impact") + 0.30 * _unit(seed, "utility") + 0.30 * _unit(seed, "adoption"))
    transmission = 10 * (0.50 * _unit(seed, "clarity") + 0.25 * _unit(seed, "codex") + 0.25 * _unit(seed, "education"))

    cost = 1 + 8 * _unit(seed, "cost")
    risk = 1 + 8 * _unit(seed, "risk")
    hype = 1 + 8 * _unit(seed, "hype")
    complexity = 1 + 8 * _unit(seed, "complexity")
    debt = 1 + 8 * _unit(seed, "debt")

    # Role/mode priors: make safety and OAK roles stricter but powerful.
    if role in {"OAK Attacker", "Negative Memory Guardian", "Test Generator"}:
        oak_score = min(1.0, oak_score + 0.12)
        risk = max(1.0, risk - 0.8)
    if mode in {"adversarial", "safety", "benchmark"}:
        oak_score = min(1.0, oak_score + 0.10)
        hype = max(1.0, hype - 1.0)
    if mode in {"creative", "meta_generation"}:
        fertility = min(10.0, fertility + 0.8)
        hype = min(9.0, hype + 0.7)
    if role in {"Prototype Forge", "Code Builder", "GitHub Operator"}:
        prototype_value = min(10.0, prototype_value + 0.9)

    score = (fertility * oak_score * reuse * prototype_value * impact * transmission) / (
        cost + risk + hype + complexity + debt + 1
    )
    status = "selected" if score >= 120 and oak_score >= 0.65 else "quarantine"
    attacks = _oak_attacks(role, mode, oak_score, hype, prototype_value)
    next_action = "decompress into codex/test/prototype" if status == "selected" else "keep compressed; improve traces or attack"
    candidate_id = f"ait-{cycle:02d}-{_hash_int(seed) % 10000:04d}"

    return AITCandidate(
        id=candidate_id,
        role=role,
        mode=mode,
        mission=mission,
        cycle=cycle,
        fertility=round(fertility, 3),
        oak_score=round(oak_score, 3),
        reuse=round(reuse, 3),
        prototype_value=round(prototype_value, 3),
        impact=round(impact, 3),
        transmission=round(transmission, 3),
        cost=round(cost, 3),
        risk=round(risk, 3),
        hype=round(hype, 3),
        complexity=round(complexity, 3),
        debt=round(debt, 3),
        score=round(score, 3),
        status=status,
        attacks=attacks,
        next_action=next_action,
    )


def generate_candidates(mission: str, cycle: int, salt: str = "") -> List[AITCandidate]:
    return [build_candidate(role, mode, mission, cycle, salt=salt) for role in ROLES for mode in MODES]


def one_page_codex(candidate: AITCandidate) -> str:
    return "\n".join(
        [
            f"# One-Page Codex — {candidate.id}",
            "",
            f"**Role:** {candidate.role}",
            f"**Mode:** {candidate.mode}",
            f"**Mission:** {candidate.mission}",
            f"**Score Ω:** {candidate.score}",
            f"**OAK:** {candidate.oak_score}",
            f"**Status:** {candidate.status}",
            "",
            "## Root",
            "Transform a goal into a verified artifact through contract, OAK, memory and prototype.",
            "",
            "## Trunk",
            "Generate → Attack → Score → Select → Decompress → Test → Memorize → Repeat.",
            "",
            "## Branches",
            f"- Primary role: {candidate.role}",
            f"- Operating mode: {candidate.mode}",
            "- Outputs: report, test plan, prototype candidate, memory update.",
            "",
            "## OAK attacks",
            *[f"- {attack}" for attack in candidate.attacks],
            "",
            "## Next action",
            candidate.next_action,
            "",
        ]
    )


def run_ait_cycle(mission: str, cycles: int = 1, salt: str = "") -> Dict[str, object]:
    all_top: List[AITCandidate] = []
    all_bottom: List[AITCandidate] = []
    history = []
    for cycle in range(cycles):
        candidates = generate_candidates(mission, cycle, salt=salt)
        ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
        top16 = ranked[:16]
        bottom16 = ranked[-16:]
        all_top = top16
        all_bottom.extend(bottom16)
        history.append(
            {
                "cycle": cycle,
                "best": asdict(top16[0]),
                "top3": [asdict(candidate) for candidate in top16[:3]],
                "bottom3": [asdict(candidate) for candidate in bottom16[:3]],
            }
        )
    best = all_top[0]
    return {
        "engine": "AIT-PANTHEON-OMEGA",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mission": mission,
        "cycles": cycles,
        "salt": salt,
        "candidate_space_per_cycle": 256,
        "dense_enumeration": False,
        "top16": [asdict(candidate) for candidate in all_top],
        "bottom16": [asdict(candidate) for candidate in sorted(all_bottom, key=lambda item: item.score)[:16]],
        "one_page_codex": one_page_codex(best),
        "history": history,
        "oak_note": "AIT architectural cycle only. No external autonomous action; promote only after tests and review.",
    }


def write_outputs(result: Dict[str, object], reports_dir: Path, memory_dir: Path, examples_dir: Path) -> None:
    reports_dir.mkdir(exist_ok=True)
    memory_dir.mkdir(exist_ok=True)
    examples_dir.mkdir(exist_ok=True)

    (reports_dir / "ait_pantheon_latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (reports_dir / "ait_pantheon_latest.md").write_text(render_markdown(result), encoding="utf-8")
    (reports_dir / "ait_pantheon_top1_codex.md").write_text(str(result["one_page_codex"]), encoding="utf-8")

    with (memory_dir / "ait_positive.jsonl").open("a", encoding="utf-8") as f:
        for candidate in result["top16"]:
            f.write(json.dumps({"type": "positive", "candidate": candidate}, ensure_ascii=False) + "\n")
    with (memory_dir / "ait_negative.jsonl").open("a", encoding="utf-8") as f:
        for candidate in result["bottom16"]:
            f.write(json.dumps({"type": "negative", "candidate": candidate}, ensure_ascii=False) + "\n")

    summary = {
        "engine": result["engine"],
        "mission": result["mission"],
        "generated_at_utc": result["generated_at_utc"],
        "top1": result["top16"][0],
        "bottom1": result["bottom16"][0],
        "oak_note": result["oak_note"],
    }
    (examples_dir / "ait_pantheon_latest.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def render_markdown(result: Dict[str, object]) -> str:
    lines = [
        "# AIT-PANTHEON-OMEGA Latest Cycle",
        "",
        f"**Generated UTC:** `{result['generated_at_utc']}`  ",
        f"**Mission:** {result['mission']}  ",
        f"**Cycles:** `{result['cycles']}`  ",
        f"**Candidate space/cycle:** `{result['candidate_space_per_cycle']}`  ",
        "",
        "> OAK: AIT architectural cycle only. No external autonomous action; promote only after tests and review.",
        "",
        "## Top 16",
        "",
        "| rank | id | role | mode | score | OAK | status |",
        "|---:|---|---|---|---:|---:|---|",
    ]
    for idx, candidate in enumerate(result["top16"], start=1):
        lines.append(
            f"| {idx} | `{candidate['id']}` | {candidate['role']} | {candidate['mode']} | {candidate['score']} | {candidate['oak_score']} | {candidate['status']} |"
        )
    lines.extend(["", "## Bottom 16 / Memory Negative", "", "| rank | id | role | mode | score | OAK |", "|---:|---|---|---|---:|---:|"])
    for idx, candidate in enumerate(result["bottom16"], start=1):
        lines.append(
            f"| {idx} | `{candidate['id']}` | {candidate['role']} | {candidate['mode']} | {candidate['score']} | {candidate['oak_score']} |"
        )
    lines.extend(["", "## Top1 Codex", "", str(result["one_page_codex"]), ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AIT-PANTHEON-OMEGA cycle.")
    parser.add_argument("--mission", default="Build better AIT systems through OAK, memory negative, FTPCI, HGFM, codex and prototypes.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--salt", default="manual")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    result = run_ait_cycle(args.mission, cycles=args.cycles, salt=args.salt)
    if args.write:
        write_outputs(result, Path("reports"), Path("memory"), Path("examples"))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
