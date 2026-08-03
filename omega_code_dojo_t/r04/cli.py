from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .analyzer import ResolutionAnalyzer
from .benchmark import run_r04_benchmark
from .engine import ResolutionEngine
from .models import ResolutionPolicy
from .portfolio import DEFAULT_PORTFOLIO


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-code-dojo-r04",
        description="Resolve and analyze large portfolios of original synthetic algorithmic fixtures.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog = subparsers.add_parser("catalog", help="List problem families and strategies.")
    catalog.add_argument("--output")

    resolve = subparsers.add_parser("resolve", help="Resolve a finite portfolio slice.")
    resolve.add_argument("--problems", type=int, default=4096)
    resolve.add_argument("--max-attempts", type=int, default=2)
    resolve.add_argument("--output")
    resolve.add_argument("--summary-only", action="store_true")

    benchmark = subparsers.add_parser("benchmark", help="Run deterministic R0.4 OAKBench.")
    benchmark.add_argument("--problems", type=int, default=4096)
    benchmark.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        _write(
            {
                "system": "omega-code-dojo-t-infinity",
                "version": "R0.4",
                "logical_problem_space": DEFAULT_PORTFOLIO.logical_problem_space,
                "families": DEFAULT_PORTFOLIO.catalog(),
            },
            args.output,
        )
        return 0
    if args.command == "resolve":
        receipt = ResolutionEngine().run(
            ResolutionPolicy(
                problem_budget=args.problems,
                max_attempts_per_problem=args.max_attempts,
                permanent_total_cap=None,
            )
        )
        payload = receipt.to_dict(include_records=not args.summary_only)
        payload["analysis"] = ResolutionAnalyzer().analyze(receipt)
        _write(payload, args.output)
        return 0 if receipt.unresolved_problems == 0 else 2
    payload = run_r04_benchmark(args.problems)
    _write(payload, args.output)
    return 0 if payload["status"] == "CERTIFIED_SYNTHETIC_PROBLEM_RESOLUTION_FIXTURES_R0_4" else 1


if __name__ == "__main__":
    raise SystemExit(main())
