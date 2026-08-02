"""Command-line interface for Ω-MAIL-T."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .engine import run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-mail",
        description="Run deterministic, sandbox-only intercompany email scenarios.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run one JSON-compatible YAML scenario")
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        report = run_scenario(args.scenario)
        payload = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(payload + "\n", encoding="utf-8")
        print(payload)
        return 0 if report["passed"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
