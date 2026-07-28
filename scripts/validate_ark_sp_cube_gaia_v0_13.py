#!/usr/bin/env python3
"""ARK-SP-CUBE-GAIA v0.13 local validation scaffold.

This script is intentionally small and dependency-free. It validates the shape of
selected JSON artifacts added in the v0.8-v0.13 integration PR. It does not
validate physical performance, carbon credit eligibility, patent status, revenue,
or public-sector decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS = [
    "experiments/checklists/ark_sp_cube_gaia_protocol_checklists_v0_12.json",
    "reports/examples/ark_sp_cube_gaia_v0_12_snapshot_bundle.json",
    "docs/oakshield_core/ARK_SP_CUBE_GAIA_OAK_LINT_RULES_v0_13.json",
]

REQUIRED_OAK_BOUNDARY_KEYS = [
    "technical_validation",
    "legal_patent_claim",
    "certified_climate_credit",
    "revenue_claim",
    "public_sector_finding",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_lint_rules(data: dict[str, Any], errors: list[str]) -> None:
    require("schema" in data, "lint rules missing schema", errors)
    require("blocked_patterns" in data, "lint rules missing blocked_patterns", errors)
    require(isinstance(data.get("blocked_patterns"), list), "blocked_patterns must be a list", errors)
    require(len(data.get("blocked_patterns", [])) >= 3, "expected at least 3 blocked patterns", errors)
    boundary = data.get("global_boundary", {})
    for key in REQUIRED_OAK_BOUNDARY_KEYS:
        require(boundary.get(key) is False, f"global_boundary.{key} must be false", errors)
    for item in data.get("blocked_patterns", []):
        require("id" in item, "blocked pattern missing id", errors)
        require("pattern" in item, "blocked pattern missing pattern", errors)
        require("severity" in item, "blocked pattern missing severity", errors)
        require("safe_rewrite" in item, "blocked pattern missing safe_rewrite", errors)


def validate_generic_json(data: Any, label: str, errors: list[str]) -> None:
    require(data is not None, f"{label} parsed as None", errors)
    if isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False).lower()
        forbidden = ["revenu garanti", "énergie du vide", "crédit carbone certifié"]
        for phrase in forbidden:
            require(phrase not in text, f"{label} contains forbidden phrase: {phrase}", errors)


def main() -> int:
    errors: list[str] = []
    loaded: dict[str, Any] = {}

    for rel in ARTIFACTS:
        path = ROOT / rel
        require(path.exists(), f"missing artifact: {rel}", errors)
        if path.exists():
            try:
                loaded[rel] = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON in {rel}: {exc}")

    for rel, data in loaded.items():
        validate_generic_json(data, rel, errors)

    lint_rel = "docs/oakshield_core/ARK_SP_CUBE_GAIA_OAK_LINT_RULES_v0_13.json"
    if isinstance(loaded.get(lint_rel), dict):
        validate_lint_rules(loaded[lint_rel], errors)

    if errors:
        print("ARK-SP-CUBE-GAIA v0.13 validation: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("ARK-SP-CUBE-GAIA v0.13 validation: PASS")
    print("Scope: JSON shape and OAK wording guardrails only.")
    print("Non-claims: no physical validation, no revenue, no certification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
