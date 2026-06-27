#!/usr/bin/env python3
"""Lint generated Omega AUTO2 reactor artifacts.

This is a local-only consistency check for artifacts produced by
omega_github_auto2_factory.py.
"""
from __future__ import annotations

import argparse
import json
import pathlib

REQUIRED_CARD_KEYS = {
    "index",
    "domain",
    "sector",
    "atom",
    "slug",
    "priority",
    "score",
    "state",
    "human_review",
    "disclosure_level",
    "oak_status",
    "proof_rule",
    "revenue_role",
    "depends_on",
    "labels",
}

ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3_STEALTH_IP", "P4_RESEARCH"}
ALLOWED_DISCLOSURES = {"public", "internal", "trade_secret", "patent_review", "never_publish_raw"}
ALLOWED_STATES = {"IDEA", "DRAFTED", "ISSUE_READY", "ISSUE_OPENED", "BRANCH_READY", "PR_READY", "CI_PASS", "OAK_PASS", "HUMAN_REVIEW", "MERGE_READY", "MERGED", "ARCHIVED_M_MINUS"}


def load_manifest(root: pathlib.Path) -> dict:
    path = root / "top1024_manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def lint_cards(cards: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(cards) != 1024:
        errors.append(f"expected 1024 cards, got {len(cards)}")
    slugs = [card.get("slug") for card in cards]
    if len(slugs) != len(set(slugs)):
        errors.append("card slugs are not unique")
    slug_set = set(slugs)
    for card in cards:
        missing = REQUIRED_CARD_KEYS - set(card)
        if missing:
            errors.append(f"card {card.get('index')} missing keys: {sorted(missing)}")
        if card.get("priority") not in ALLOWED_PRIORITIES:
            errors.append(f"card {card.get('slug')} has bad priority")
        if card.get("disclosure_level") not in ALLOWED_DISCLOSURES:
            errors.append(f"card {card.get('slug')} has bad disclosure")
        if card.get("state") not in ALLOWED_STATES:
            errors.append(f"card {card.get('slug')} has bad state")
        for dep in card.get("depends_on", []):
            if dep not in slug_set:
                errors.append(f"card {card.get('slug')} depends on missing {dep}")
        if card.get("disclosure_level") in {"patent_review", "trade_secret", "never_publish_raw"} and not card.get("human_review"):
            errors.append(f"sensitive card lacks human review: {card.get('slug')}")
        if card.get("atom") == "pricing_meter" and not card.get("human_review"):
            errors.append(f"pricing card lacks human review: {card.get('slug')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="artifacts/omega_github_auto2")
    args = parser.parse_args()
    manifest = load_manifest(pathlib.Path(args.root))
    errors = lint_cards(manifest.get("cards", []))
    if errors:
        print("Omega AUTO2 lint failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Omega AUTO2 lint passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
