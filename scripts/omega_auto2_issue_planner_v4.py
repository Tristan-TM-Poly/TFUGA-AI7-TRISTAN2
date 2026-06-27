#!/usr/bin/env python3
"""Omega AUTO2 v4 safe issue planner.

Manual, auditable issue planner for a small P0 batch.

Default mode is dry-run. Creating issues requires --execute. The script is
intended for GitHub Actions workflow_dispatch or local maintainer use.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

P0_ALLOWLIST = [
    "api_gateway_input_schema_v1",
    "api_gateway_output_schema_v1",
    "api_gateway_core_algorithm_v1",
    "api_gateway_oak_gate_v1",
    "usage_metering_input_schema_v1",
    "usage_metering_core_algorithm_v1",
    "axis_validation_core_algorithm_v1",
    "schema_validation_core_algorithm_v1",
]

DEFAULT_LABELS = ["omega-auto2", "zero-touch"]


def run_command(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or f"Command failed: {' '.join(cmd)}"
        raise RuntimeError(message)
    return result.stdout.strip()


def load_manifest(path: pathlib.Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cards = data.get("cards")
    if not isinstance(cards, list):
        raise ValueError("Expected a generated manifest with a top-level cards list")
    return cards


def select_cards(cards: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_slug = {card["slug"]: card for card in cards}
    selected: list[dict[str, Any]] = []
    for slug in P0_ALLOWLIST:
        card = by_slug.get(slug)
        if card is not None:
            selected.append(card)
        if len(selected) >= limit:
            break
    return selected


def issue_title(card: dict[str, Any]) -> str:
    return f"Omega AUTO2 P0: {card['slug']}"


def issue_body(card: dict[str, Any], control_issue: int | None) -> str:
    parent = f"Parent control issue: #{control_issue}\n\n" if control_issue else ""
    return f"""# Omega AUTO2 P0 Card: {card['slug']}

{parent}## Goal

Materialize `{card['slug']}` as a small, reviewable, OAK-safe micro-asset.

## Card metadata

- Domain: `{card['domain']}`
- Sector: `{card['sector']}`
- Atom: `{card['atom']}`
- Priority: `{card['priority']}`
- Score: `{card['score']}`
- Disclosure: `{card['disclosure_level']}`
- Human review: `{card['human_review']}`

## Deliverables

- Documentation for the card.
- Synthetic fixture.
- Baseline or validation rule.
- OAK pass/fail rule.
- M-minus failure note.
- Future PR implementation checklist.

## OAK checks

- Synthetic examples only.
- No production billing.
- No external outreach.
- No sensitive IP disclosure.
- No regulated-domain claim.
- Failure modes documented.

## Done when

- The card is specific enough to become one future PR.
- A testable next action is clear.
"""


def issue_exists(title: str) -> bool:
    output = run_command([
        "gh",
        "issue",
        "list",
        "--state",
        "open",
        "--search",
        f"{title} in:title",
        "--json",
        "number,title",
    ])
    return bool(json.loads(output))


def create_issue(card: dict[str, Any], labels: list[str], control_issue: int | None) -> str:
    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        issue_title(card),
        "--body",
        issue_body(card, control_issue),
    ]
    for label in labels:
        cmd += ["--label", label]
    return run_command(cmd)


def write_audit(path: pathlib.Path, audit: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="artifacts/omega_github_auto2/top1024_manifest.json")
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--delay-seconds", type=int, default=10)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--control-issue", type=int, default=None)
    parser.add_argument("--audit-out", default="artifacts/omega_auto2_issue_planner_v4/audit.json")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 8:
        raise ValueError("--limit must be between 1 and 8")
    if args.delay_seconds < 0 or args.delay_seconds > 60:
        raise ValueError("--delay-seconds must be between 0 and 60")

    cards = load_manifest(pathlib.Path(args.manifest))
    selected = select_cards(cards, args.limit)
    audit: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "execute" if args.execute else "dry_run",
        "limit": args.limit,
        "selected": [],
    }

    for card in selected:
        title = issue_title(card)
        item: dict[str, Any] = {"slug": card["slug"], "title": title, "status": "planned"}
        if args.execute:
            if issue_exists(title):
                item["status"] = "skipped_existing"
            else:
                item["url"] = create_issue(card, DEFAULT_LABELS, args.control_issue)
                item["status"] = "created"
                time.sleep(args.delay_seconds)
        audit["selected"].append(item)

    write_audit(pathlib.Path(args.audit_out), audit)
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
