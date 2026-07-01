"""Local validator for Ω-AUTO²-OAK-FIXALL-T decision JSON files.

Side-effect free: reads a JSON file and validates basic OAK decision invariants.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_DECISIONS = {
    "MERGE_NOW",
    "REPAIR_SAFE",
    "WAIT_COOLDOWN",
    "BLOCK_M_MINUS",
    "HUMAN_APPROVAL_REQUIRED",
}

REQUIRED_KEYS = {
    "repo",
    "item_type",
    "item_id",
    "observed_state",
    "blockers",
    "decision",
    "oak_constraints",
    "next_action",
}


def validate_decision(data: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        errors.append(f"missing required keys: {missing}")

    decision = data.get("decision")
    if decision not in VALID_DECISIONS:
        errors.append(f"invalid decision: {decision!r}")

    blockers = data.get("blockers")
    if not isinstance(blockers, list):
        errors.append("blockers must be a list")

    constraints = data.get("oak_constraints")
    if not isinstance(constraints, dict):
        errors.append("oak_constraints must be an object")
    else:
        for key in ["non_destructive", "no_secret_exposure", "no_bypass", "human_sensitive_safe"]:
            if constraints.get(key) is not True:
                errors.append(f"oak constraint must be true: {key}")

    state = data.get("observed_state")
    if not isinstance(state, dict):
        errors.append("observed_state must be an object")
    else:
        if decision == "MERGE_NOW":
            expected = {
                "open": True,
                "draft": False,
                "mergeable": True,
                "checks_state": "green",
            }
            for key, value in expected.items():
                if state.get(key) != value:
                    errors.append(f"MERGE_NOW requires {key}={value!r}")
            if blockers:
                errors.append("MERGE_NOW requires an empty blocker list")

        if state.get("draft") is True and decision == "MERGE_NOW":
            errors.append("draft items cannot be MERGE_NOW")

        if state.get("mergeable") is False and decision == "MERGE_NOW":
            errors.append("non-mergeable items cannot be MERGE_NOW")

    return errors


def validate_file(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return validate_decision(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Ω-AUTO2-OAK-FIXALL decision JSON file.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        errors = validate_file(path)
        if errors:
            failed = True
            print(f"{path}: FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{path}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
