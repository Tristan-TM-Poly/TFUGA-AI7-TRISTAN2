#!/usr/bin/env python3
"""Generate Omega AUTO2 planning artifacts from a JSON configuration.

This script is offline-only: it writes local JSON/Markdown artifacts for GitHub
review and does not call external APIs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone


def load_config(path: str) -> dict:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    assert len(data["domains"]) == 16
    assert len(data["card_template"]) == 16
    for domain in data["domains"]:
        assert len(domain["sectors"]) == 4
    return data


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def score_card(config: dict, sector: str, atom: str) -> float:
    weights = config["score_weights"]
    values = dict(config["score_defaults"])
    if sector in config.get("p0_sectors", []):
        values.update({"revenue_short_term": 90, "proof_measurable": 85, "market_demand": 88, "zero_touch": 90, "api_scalability": 90})
    if sector in config.get("stealth_ip_sectors", []):
        values.update({"proof_measurable": 75, "ip_potential": 95, "b2b_compliance": 75})
    if atom in {"oak_gate", "benchmark_suite", "failure_mode_registry", "mminus_logger"}:
        values["proof_measurable"] = max(values["proof_measurable"], 88)
        values["moat_retention"] = max(values["moat_retention"], 80)
    return round(sum(weights[k] * values[k] for k in weights), 2)


def priority(config: dict, sector: str, score: float) -> str:
    if sector in config.get("p0_sectors", []):
        return "P0"
    if sector in config.get("stealth_ip_sectors", []):
        return "P3_REVIEW"
    if score >= 80:
        return "P1"
    if score >= 65:
        return "P2"
    return "P4"


def build_cards(config: dict) -> list[dict]:
    cards = []
    idx = 1
    for domain in config["domains"]:
        for sector in domain["sectors"]:
            for atom in config["card_template"]:
                s = score_card(config, sector, atom)
                cards.append({
                    "index": idx,
                    "domain": domain["name"],
                    "sector": sector,
                    "atom": atom,
                    "slug": f"{slug(sector)}_{slug(atom)}_v1",
                    "priority": priority(config, sector, s),
                    "score": s,
                    "human_review": sector in config.get("stealth_ip_sectors", []) or atom == "pricing_meter"
                })
                idx += 1
    assert len(cards) == 1024
    return cards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/omega_github_auto2_top1024.json")
    parser.add_argument("--out", default="artifacts/omega_github_auto2")
    parser.add_argument("--issue-limit", type=int, default=16)
    args = parser.parse_args()

    config = load_config(args.config)
    cards = build_cards(config)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "top1024_manifest.json").write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "cards": cards}, indent=2), encoding="utf-8")

    top64 = sorted(cards, key=lambda c: (c["priority"] != "P0", -c["score"], c["index"]))[:64]
    lines = ["# Omega AUTO2 Top64 Execution Queue", "", "| # | card | priority | score | review |", "|---:|---|---|---:|---|"]
    for card in top64:
        lines.append(f"| {card['index']} | `{card['slug']}` | {card['priority']} | {card['score']} | {card['human_review']} |")
    (out / "top64_execution_queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    drafts = out / "issue_drafts"
    drafts.mkdir(exist_ok=True)
    for card in top64[:args.issue_limit]:
        body = f"# Omega AUTO2 card {card['index']}: {card['slug']}\n\nPriority: {card['priority']}\nScore: {card['score']}\nHuman review: {card['human_review']}\n\nRequired: schema, baseline, OAK gate, M- log, test fixture, report note.\n"
        (drafts / f"{card['index']:04d}_{card['slug']}.md").write_text(body, encoding="utf-8")

    oak = {"status": "PASS", "card_count_is_1024": len(cards) == 1024, "top64_count": len(top64)}
    (out / "oak_report.json").write_text(json.dumps(oak, indent=2), encoding="utf-8")
    print(f"Generated {len(cards)} cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
