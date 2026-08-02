"""Deterministic policy atlas for legal-production action classes.

The dimensions are a versioned taxonomy, not an execution cap. Future versions
may add dimensions without changing the action engine's resource budgets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .models import ActionType, hash_payload


RISK_MODES = (
    "routine",
    "identity_uncertain",
    "authority_uncertain",
    "financial_exposure",
    "personal_information",
    "ip_exposure",
    "regulatory_attestation",
    "irreversible_effect",
)
AUTONOMY_LEVELS = ("L0_DOCUMENT", "L1_PREPARE", "L2_VALIDATE", "L3_PROVIDER_DRAFT", "L4_BOUNDED", "L5_APPROVED", "L6_POLICY_CLASS")
LAYERS = ("plan", "gate", "evidence")


def _cell(action_type: ActionType, risk_mode: str, autonomy: str, layer: str) -> dict[str, Any]:
    professional = action_type in {
        ActionType.SIGNATURE,
        ActionType.GOVERNMENT_FILING,
        ActionType.INCORPORATION,
    } or risk_mode in {"regulatory_attestation", "irreversible_effect"}
    two_approvals = risk_mode in {"financial_exposure", "irreversible_effect"} or action_type == ActionType.INCORPORATION
    external_effect = autonomy in {"L4_BOUNDED", "L5_APPROVED", "L6_POLICY_CLASS"}
    if external_effect and professional:
        decision = "PROFESSIONAL_REVIEW"
    elif external_effect and two_approvals:
        decision = "REQUIRE_TWO_APPROVALS"
    elif external_effect:
        decision = "REQUIRE_APPROVAL"
    else:
        decision = "ALLOW_DRY_RUN"
    payload = {
        "action_type": action_type.value,
        "risk_mode": risk_mode,
        "autonomy": autonomy,
        "layer": layer,
        "decision": decision,
        "professional_review": professional,
        "two_approvals": two_approvals,
        "external_effect": external_effect,
    }
    payload["cell_hash"] = hash_payload(payload)
    return payload


def generate(root: str | Path) -> dict[str, Any]:
    destination = Path(root)
    destination.mkdir(parents=True, exist_ok=True)
    shards = destination / "shards"
    shards.mkdir(exist_ok=True)
    files: list[dict[str, Any]] = []
    total = 0
    for action_type in ActionType:
        for risk_mode in RISK_MODES:
            path = shards / f"{action_type.value.casefold()}__{risk_mode}.jsonl"
            rows = [
                _cell(action_type, risk_mode, autonomy, layer)
                for autonomy in AUTONOMY_LEVELS
                for layer in LAYERS
            ]
            rendered = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
            path.write_text(rendered, encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()
            files.append({"path": str(path.relative_to(destination)), "rows": len(rows), "sha256": digest})
            total += len(rows)
    manifest = {
        "schema": "omega-legal-production-atlas-v1",
        "dimensions": {
            "action_types": len(ActionType),
            "risk_modes": len(RISK_MODES),
            "autonomy_levels": len(AUTONOMY_LEVELS),
            "layers": len(LAYERS),
        },
        "expected_cells": len(ActionType) * len(RISK_MODES) * len(AUTONOMY_LEVELS) * len(LAYERS),
        "actual_cells": total,
        "shards": files,
    }
    manifest["manifest_hash"] = hash_payload(manifest)
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def audit(root: str | Path) -> dict[str, Any]:
    destination = Path(root)
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    cells = 0
    for item in manifest.get("shards", []):
        path = destination / item["path"]
        if not path.exists():
            errors.append(f"missing:{item['path']}")
            continue
        rendered = path.read_text(encoding="utf-8")
        digest = "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if digest != item["sha256"]:
            errors.append(f"digest:{item['path']}")
        lines = [line for line in rendered.splitlines() if line.strip()]
        if len(lines) != item["rows"]:
            errors.append(f"rows:{item['path']}")
        for line in lines:
            row = json.loads(line)
            supplied = row.pop("cell_hash")
            if supplied != hash_payload(row):
                errors.append(f"cell_hash:{item['path']}")
        cells += len(lines)
    if cells != manifest.get("expected_cells"):
        errors.append("cardinality")
    return {
        "valid": not errors,
        "cells": cells,
        "shards": len(manifest.get("shards", [])),
        "expected_cells": manifest.get("expected_cells"),
        "errors": errors,
        "manifest_hash": manifest.get("manifest_hash"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-legal-atlas")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "audit"):
        command = sub.add_parser(name)
        command.add_argument("root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = generate(args.root) if args.command == "generate" else audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
