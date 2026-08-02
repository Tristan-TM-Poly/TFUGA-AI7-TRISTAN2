"""CLI for real, explicitly authorized provider execution."""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from .real_execution import doctor, execute_action, reconcile_action
from .real_providers import PROVIDERS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-legal-real",
        description=(
            "Execute one exact approved action through a real provider. "
            "No provider is called without exact environment interlocks."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = commands.add_parser("doctor", help="Check provider environment without printing secrets")
    doctor_parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    doctor_parser.add_argument("--allow-missing", action="store_true")

    execute_parser = commands.add_parser("execute", help="Reserve and execute one exact approved action")
    execute_parser.add_argument("action")
    execute_parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    execute_parser.add_argument("--ledger", required=True)
    execute_parser.add_argument("--receipt", required=True)

    reconcile_parser = commands.add_parser("reconcile", help="Query provider state for a prior receipt")
    reconcile_parser.add_argument("action")
    reconcile_parser.add_argument("receipt")
    reconcile_parser.add_argument("--ledger", required=True)
    reconcile_parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        result = doctor(args.provider)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] or args.allow_missing else 2
    if args.command == "execute":
        result = execute_action(
            args.action,
            provider_name=args.provider,
            ledger_path=args.ledger,
            receipt_path=args.receipt,
        )
        print(json.dumps(result.to_mapping(), indent=2, sort_keys=True))
        return 0
    result = reconcile_action(
        args.action,
        args.receipt,
        ledger_path=args.ledger,
        output_path=args.output,
    )
    print(json.dumps(result.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
