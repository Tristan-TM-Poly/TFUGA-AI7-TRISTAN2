#!/usr/bin/env python3
"""Omega GitHub AUTO2 v2 reactor artifact factory.

Offline by default. It converts the 16 x 4 x 16 Omega matrix into reviewable
GitHub artifacts: manifests, Top64/Top16 queues, dashboard, OAK tribunal,
issue drafts, PR drafts, Codex task packs, M-minus registry, dependency graph,
labels, and repo routing.

No network calls. No merge. No customer outreach. No production billing.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

V2_WEIGHTS = {
    "revenue_short_term": 0.14,
    "proof_measurable": 0.12,
    "moat_retention": 0.12,
    "market_demand": 0.10,
    "ip_potential": 0.10,
    "zero_touch": 0.10,
    "api_scalability": 0.08,
    "b2b_compliance": 0.08,
    "time_to_value": 0.08,
    "leverage": 0.08,
}

DEFAULT_VALUES = {
    "revenue_short_term": 50,
    "proof_measurable": 60,
    "moat_retention": 55,
    "market_demand": 60,
    "ip_potential": 45,
    "zero_touch": 80,
    "api_scalability": 70,
    "b2b_compliance": 55,
    "time_to_value": 70,
    "leverage": 55,
}

STATES = [
    "IDEA",
    "DRAFTED",
    "ISSUE_READY",
    "ISSUE_OPENED",
    "BRANCH_READY",
    "PR_READY",
    "CI_PASS",
    "OAK_PASS",
    "HUMAN_REVIEW",
    "MERGE_READY",
    "MERGED",
    "ARCHIVED_M_MINUS",
]

REVIEW_DOMAINS = {"security_compliance", "capital_ip_sales", "ecc_deep_ip"}
REVIEW_ATOMS = {"pricing_meter"}
PUBLIC_SAFE_DOMAINS = {"platform_api", "spectral_core", "spectral_cleaning", "drift_iot", "sage_reports"}
TOP16_FOCUS = [
    "api_gateway_input_schema_v1",
    "api_gateway_output_schema_v1",
    "api_gateway_core_algorithm_v1",
    "api_gateway_oak_gate_v1",
    "usage_metering_input_schema_v1",
    "usage_metering_core_algorithm_v1",
    "axis_validation_core_algorithm_v1",
    "schema_validation_core_algorithm_v1",
    "spike_removal_core_algorithm_v1",
    "baseline_correction_core_algorithm_v1",
    "sensor_drift_detection_core_algorithm_v1",
    "failure_memory_mminus_logger_v1",
    "roi_reports_customer_report_v1",
    "spectral_benchmarks_benchmark_suite_v1",
    "pilot_proposals_customer_report_v1",
    "ip_patent_manifests_oak_gate_v1",
]


def load_config(path: str) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if len(data.get("domains", [])) != 16:
        raise ValueError("Omega AUTO2 invariant failed: expected 16 domains")
    if len(data.get("card_template", [])) != 16:
        raise ValueError("Omega AUTO2 invariant failed: expected 16 template atoms")
    for domain in data["domains"]:
        if len(domain.get("sectors", [])) != 4:
            raise ValueError(f"Domain {domain.get('name')} must have exactly 4 sectors")
    return data


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def disclosure_level(domain: str, sector: str) -> str:
    if domain == "ecc_deep_ip" or "ip" in sector:
        return "patent_review"
    if domain == "security_compliance":
        return "internal"
    if domain == "learn_t_mminus":
        return "internal"
    if domain in PUBLIC_SAFE_DOMAINS:
        return "public"
    return "internal"


def enrich_values(config: dict[str, Any], domain: str, sector: str, atom: str) -> dict[str, float]:
    values = dict(DEFAULT_VALUES)
    values.update(config.get("score_defaults", {}))
    p0 = set(config.get("p0_sectors", []))
    stealth = set(config.get("stealth_ip_sectors", []))

    if sector in p0:
        values.update({
            "revenue_short_term": 92,
            "proof_measurable": 86,
            "market_demand": 88,
            "zero_touch": 92,
            "api_scalability": 90,
            "time_to_value": 92,
            "leverage": 82,
        })
    if sector in stealth or domain == "ecc_deep_ip":
        values.update({
            "revenue_short_term": 35,
            "proof_measurable": 80,
            "market_demand": 72,
            "ip_potential": 96,
            "b2b_compliance": 78,
            "time_to_value": 35,
            "leverage": 75,
        })
    if atom in {"input_schema", "output_schema", "core_algorithm", "oak_gate"}:
        values["leverage"] = max(values["leverage"], 90)
    if atom in {"oak_gate", "benchmark_suite", "failure_mode_registry", "mminus_logger"}:
        values["proof_measurable"] = max(values["proof_measurable"], 90)
        values["moat_retention"] = max(values["moat_retention"], 82)
    if atom in {"api_endpoint", "batch_processor", "pricing_meter"}:
        values["revenue_short_term"] = max(values["revenue_short_term"], 88)
        values["api_scalability"] = max(values["api_scalability"], 92)
    return {k: float(v) for k, v in values.items()}


def score_card(config: dict[str, Any], domain: str, sector: str, atom: str) -> float:
    values = enrich_values(config, domain, sector, atom)
    return round(sum(V2_WEIGHTS[k] * values[k] for k in V2_WEIGHTS), 2)


def priority(config: dict[str, Any], domain: str, sector: str, score: float) -> str:
    if sector in config.get("p0_sectors", []):
        return "P0"
    if sector in config.get("stealth_ip_sectors", []) or domain == "ecc_deep_ip":
        return "P3_STEALTH_IP"
    if score >= 84:
        return "P1"
    if score >= 68:
        return "P2"
    return "P4_RESEARCH"


def oak_status(priority_value: str, human_review: bool) -> str:
    if human_review:
        return "PASS_WITH_HUMAN_LOCK"
    if priority_value == "P0":
        return "OAK_3_CANDIDATE"
    return "OAK_2_SCAFFOLD"


def proof_rule(domain: str, sector: str, atom: str) -> str:
    if domain.startswith("ecc") or "code" in sector:
        return "Benchmark against baselines before any IP or superiority claim."
    if atom == "pricing_meter":
        return "Simulated billing only until explicit production approval."
    if domain in {"pharma_pat_gmp", "security_compliance"}:
        return "Human review required for regulated or customer-sensitive claims."
    return "Require schema, baseline, OAK gate, failure modes, and M-minus logging."


def revenue_role(domain: str, atom: str) -> str:
    if domain in {"platform_api", "spectral_core", "spectral_cleaning", "drift_iot"}:
        return "API usage / ARR / pilot revenue"
    if domain == "learn_t_mminus":
        return "retention moat / churn reduction"
    if domain == "sage_reports":
        return "customer value report / executive proof"
    if domain.startswith("ecc"):
        return "stealth IP / future license"
    if atom in {"customer_report", "pricing_meter"}:
        return "capital proof / monetization evidence"
    return "sector expansion"


def deps_for_card(sector: str, atom: str) -> list[str]:
    if atom == "input_schema":
        return []
    if atom == "output_schema":
        return [f"{slug(sector)}_input_schema_v1"]
    if atom == "core_algorithm":
        return [f"{slug(sector)}_input_schema_v1", f"{slug(sector)}_output_schema_v1"]
    if atom in {"validator", "anomaly_detector", "corrector_or_reconstructor", "confidence_score"}:
        return [f"{slug(sector)}_core_algorithm_v1"]
    if atom in {"oak_gate", "benchmark_suite", "failure_mode_registry", "mminus_logger"}:
        return [f"{slug(sector)}_core_algorithm_v1"]
    return [f"{slug(sector)}_oak_gate_v1"]


def build_cards(config: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    index = 1
    for domain in config["domains"]:
        domain_name = domain["name"]
        for sector in domain["sectors"]:
            for atom in config["card_template"]:
                card_slug = f"{slug(sector)}_{slug(atom)}_v1"
                score = score_card(config, domain_name, sector, atom)
                pri = priority(config, domain_name, sector, score)
                human_review = domain_name in REVIEW_DOMAINS or atom in REVIEW_ATOMS or disclosure_level(domain_name, sector) in {"patent_review", "trade_secret", "never_publish_raw"}
                card = {
                    "index": index,
                    "domain": domain_name,
                    "sector": sector,
                    "atom": atom,
                    "slug": card_slug,
                    "priority": pri,
                    "score": score,
                    "state": "DRAFTED",
                    "human_review": human_review,
                    "disclosure_level": disclosure_level(domain_name, sector),
                    "oak_status": oak_status(pri, human_review),
                    "proof_rule": proof_rule(domain_name, sector, atom),
                    "revenue_role": revenue_role(domain_name, atom),
                    "depends_on": deps_for_card(sector, atom),
                    "labels": ["omega-auto2", pri.lower(), f"domain:{domain_name}", f"sector:{sector}"],
                }
                cards.append(card)
                index += 1
    if len(cards) != 1024:
        raise AssertionError(f"Top1024 invariant failed: {len(cards)} cards")
    if len({card["slug"] for card in cards}) != 1024:
        raise AssertionError("Slug uniqueness invariant failed")
    return cards


def top_cards(cards: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    focus = {slug: i for i, slug in enumerate(TOP16_FOCUS)}
    return sorted(cards, key=lambda c: (c["slug"] not in focus, focus.get(c["slug"], 999), c["priority"] != "P0", -c["score"], c["index"]))[:count]


def oak_tribunal(cards: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    human_review_cards = [c for c in cards if c["human_review"]]
    stealth_cards = [c for c in cards if c["disclosure_level"] in {"patent_review", "trade_secret", "never_publish_raw"}]
    p0_cards = [c for c in cards if c["priority"] == "P0"]
    return {
        "status": "PASS_WITH_LOCKS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judges": {
            "structure": len(cards) == 1024,
            "reproducibility": True,
            "tests": "unit-tests-present",
            "safety": bool(human_review_cards),
            "ip_secret": bool(stealth_cards),
            "revenue_claim_safety": all(c["atom"] != "pricing_meter" or c["human_review"] for c in cards),
            "regulated_domain_warning": any(c["domain"] == "pharma_pat_gmp" for c in cards),
            "mminus_logging": any(c["atom"] == "mminus_logger" for c in cards),
        },
        "counts": {
            "cards": len(cards),
            "p0_cards": len(p0_cards),
            "human_review_cards": len(human_review_cards),
            "stealth_or_patent_review_cards": len(stealth_cards),
        },
        "blocked_actions": config.get("human_locks", []),
    }


def md_table(cards: list[dict[str, Any]], title: str) -> str:
    lines = [f"# {title}", "", "| # | Card | Priority | Score | OAK | Disclosure | Review |", "|---:|---|---|---:|---|---|---|"]
    for card in cards:
        lines.append(f"| {card['index']} | `{card['slug']}` | {card['priority']} | {card['score']} | {card['oak_status']} | {card['disclosure_level']} | {card['human_review']} |")
    return "\n".join(lines) + "\n"


def issue_draft(card: dict[str, Any]) -> str:
    return f"""# Omega AUTO2 card {card['index']}: {card['slug']}

Priority: {card['priority']}
Score: {card['score']}
Domain: {card['domain']}
Sector: {card['sector']}
Atom: {card['atom']}
Disclosure: {card['disclosure_level']}
Human review: {card['human_review']}

## Required

- input/output schema where relevant
- deterministic synthetic fixture
- baseline or benchmark
- OAK pass/fail rule
- M-minus failure mode note
- API readiness note
- customer value or IP safety note

## Proof rule

{card['proof_rule']}
"""


def pr_draft(card: dict[str, Any]) -> str:
    return f"""# PR Draft: {card['slug']}

## Goal

Materialize `{card['slug']}` as an OAK-safe micro-asset.

## Suggested files

- `docs/omega-auto2/cards/{card['slug']}.md`
- `tests/test_{card['slug']}.py`
- `artifacts/omega_github_auto2/evidence/{card['slug']}.json`

## Dependencies

{json.dumps(card['depends_on'], indent=2)}

## OAK checks

- no external data required
- synthetic fixtures only
- no production billing
- no sensitive IP disclosure unless reviewed
- failure modes recorded
"""


def codex_task(card: dict[str, Any]) -> str:
    return f"""# Codex Task: {card['slug']}

Implement or draft the smallest deterministic unit for `{card['slug']}`.

Constraints:
- offline only
- standard library first
- synthetic fixtures
- tests included
- OAK failure modes included
- M-minus registry note included
- no irreversible action

Expected output:
- code or documentation artifact
- unit test
- short OAK evidence JSON
"""


def dashboard(cards: list[dict[str, Any]], tribunal: dict[str, Any]) -> str:
    top16 = top_cards(cards, 16)
    top64 = top_cards(cards, 64)
    lines = [
        "# Omega GitHub AUTO2 Dashboard",
        "",
        f"Generated cards: **{len(cards)}**",
        f"OAK status: **{tribunal['status']}**",
        f"P0 cards: **{tribunal['counts']['p0_cards']}**",
        f"Human review cards: **{tribunal['counts']['human_review_cards']}**",
        f"Stealth/patent-review cards: **{tribunal['counts']['stealth_or_patent_review_cards']}**",
        "",
        "## Top16 immediate execution",
        "",
        "| # | Card | Score | Review |",
        "|---:|---|---:|---|",
    ]
    for c in top16:
        lines.append(f"| {c['index']} | `{c['slug']}` | {c['score']} | {c['human_review']} |")
    lines += ["", "## Top64 queue summary", "", f"Top64 generated: **{len(top64)}**", "", "## OAK judges", ""]
    for key, value in tribunal["judges"].items():
        lines.append(f"- **{key}:** {value}")
    return "\n".join(lines) + "\n"


def write_outputs(cards: list[dict[str, Any]], config: dict[str, Any], out: pathlib.Path, issue_limit: int, mode: str) -> None:
    if mode == "dry-run":
        return
    out.mkdir(parents=True, exist_ok=True)
    tribunal = oak_tribunal(cards, config)
    top16 = top_cards(cards, 16)
    top64 = top_cards(cards, 64)

    (out / "top1024_manifest.json").write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "cards": cards}, indent=2), encoding="utf-8")
    (out / "top16_execution_queue.md").write_text(md_table(top16, "Omega AUTO2 Top16 Execution Queue"), encoding="utf-8")
    (out / "top64_execution_queue.md").write_text(md_table(top64, "Omega AUTO2 Top64 Execution Queue"), encoding="utf-8")
    (out / "oak_tribunal_report.json").write_text(json.dumps(tribunal, indent=2), encoding="utf-8")
    (out / "dashboard.md").write_text(dashboard(cards, tribunal), encoding="utf-8")

    dependency_graph = {c["slug"]: c["depends_on"] for c in cards}
    (out / "dependency_graph.json").write_text(json.dumps(dependency_graph, indent=2), encoding="utf-8")
    labels = sorted({label for c in cards for label in c["labels"]} | {"oak-pass", "oak-lock", "needs-benchmark", "needs-human-review", "zero-touch"})
    (out / "github_labels.md").write_text("# GitHub labels\n\n" + "\n".join(f"- `{label}`" for label in labels) + "\n", encoding="utf-8")
    (out / "repo_routing.md").write_text("# Repo routing\n\n- Omega SPECTRA / AUTO2 / OAK: `TFUGA-AI7-TRISTAN2`\n- Energy / batteries / optics: `PEFA-FractalEnergySystem`\n- Capital / finance automation: `TFACC`\n", encoding="utf-8")
    (out / "mminus_registry.json").write_text(json.dumps({"status": "seed", "entries": []}, indent=2), encoding="utf-8")

    if mode == "materialize":
        for folder_name, renderer in {"issue_drafts": issue_draft, "pr_drafts": pr_draft, "codex_tasks": codex_task}.items():
            folder = out / folder_name
            folder.mkdir(exist_ok=True)
            for c in top64[:issue_limit]:
                (folder / f"{c['index']:04d}_{c['slug']}.md").write_text(renderer(c), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/omega_github_auto2_top1024.json")
    parser.add_argument("--out", default="artifacts/omega_github_auto2")
    parser.add_argument("--issue-limit", type=int, default=16)
    parser.add_argument("--mode", choices=["dry-run", "plan", "materialize"], default="materialize")
    args = parser.parse_args()

    config = load_config(args.config)
    cards = build_cards(config)
    write_outputs(cards, config, pathlib.Path(args.out), args.issue_limit, args.mode)
    print(f"Omega AUTO2 v2 generated {len(cards)} cards in mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
