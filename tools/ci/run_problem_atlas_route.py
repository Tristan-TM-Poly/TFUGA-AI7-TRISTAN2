from __future__ import annotations

import argparse
import glob
import json
import subprocess
from pathlib import Path
from typing import Iterable

from omega_ci_admission_t.core import load_config

CONFIG = Path("config/omega_ci_admission/problem_atlas_routes.json")


def _expand_args(args: Iterable[str]) -> list[str]:
    result: list[str] = []
    for index, value in enumerate(args):
        if index == 0:
            result.append(value)
            continue
        if any(character in value for character in "*?["):
            matches = sorted(glob.glob(value))
            if not matches:
                raise ValueError(f"suite glob matched no files: {value}")
            result.extend(matches)
        else:
            result.append(value)
    return result


def _lookup(kind: str, item_id: str) -> tuple[list[str], dict]:
    config = load_config(CONFIG)
    if kind == "route":
        for route in config.routes:
            if route.route_id == item_id:
                return _expand_args(route.suite_args), route.to_dict()
    else:
        for validator in config.validators:
            if validator.validator_id == item_id:
                return _expand_args(validator.command_args), validator.to_dict()
    raise KeyError(f"unknown {kind}: {item_id}")


def _validate_command(args: list[str]) -> None:
    if not args:
        raise ValueError("command cannot be empty")
    if args[0] not in {"pytest", "python"}:
        raise ValueError(f"unsupported executable: {args[0]}")
    forbidden_fragments = (";", "&&", "||", "|", ">", "<", "`", "$(", "\n", "\r")
    if any(fragment in item for item in args for fragment in forbidden_fragments):
        raise ValueError("command argument contains forbidden shell syntax")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("route", "validator"), required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--receipt-output")
    parsed = parser.parse_args()

    command, policy = _lookup(parsed.kind, parsed.id)
    _validate_command(command)
    completed = subprocess.run(command, check=False, shell=False)
    receipt = {
        "schema": "omega-ci-suite-execution-receipt/1",
        "kind": parsed.kind,
        "id": parsed.id,
        "command": command,
        "returncode": completed.returncode,
        "policy": policy,
        "shell": False,
        "network_action_performed": False,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
    }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if parsed.receipt_output:
        output = Path(parsed.receipt_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
