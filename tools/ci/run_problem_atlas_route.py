from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from omega_ci_admission_t.model import load_route_config

CONFIG = Path("config/omega_ci_admission/problem_atlas_routes.json")


def _safe_command(command: str) -> list[str]:
    forbidden = {";", "&&", "||", "|", ">", "<", "`", "$(``, "\n"}
    if any(token in command for token in forbidden):
        raise ValueError("suite command contains forbidden shell syntax")
    parts = shlex.split(command)
    if not parts:
        raise ValueError("suite command cannot be empty")
    if parts[0] not in {"pytest", "python"}:
        raise ValueError(f"unsupported suite executable: {parts[0]}")
    return parts


def _lookup(kind: str, item_id: str) -> tuple[str, dict[str, Any]]:
    config = load_route_config(CONFIG)
    if kind == "route":
        for route in config.routes:
            if route.route_id == item_id:
                return route.suite_command, route.to_dict()
    elif kind == "validator":
        for validator in config.shared_validators:
            if validator.validator_id == item_id:
                return validator.suite_command, validator.to_dict()
    raise KeyError(f"unknown {kind}: {item_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("route", "validator"), required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--receipt-output")
    args = parser.parse_args()

    command, policy = _lookup(args.kind, args.id)
    parts = _safe_command(command)
    completed = subprocess.run(parts, check=False, shell=False)
    receipt = {
        "schema": "omega-ci-suite-execution-receipt/1",
        "kind": args.kind,
        "id": args.id,
        "command": parts,
        "returncode": completed.returncode,
        "policy": policy,
        "shell": False,
        "network_action_performed": False,
        "workflow_mutation_performed": False,
        "workflow_cancellation_performed": False,
    }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt_output:
        output = Path(args.receipt_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
