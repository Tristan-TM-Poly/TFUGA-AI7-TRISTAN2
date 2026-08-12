"""CLI for MetaScienceBench-T v0.1."""

from __future__ import annotations

import argparse
import json

from .benchmark import report_as_dict, run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-meta-science",
        description="Run the deterministic Ω-META-SCIENCE-FOUNDRY-T MetaScienceBench v0.1.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit compact JSON instead of indented JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = report_as_dict(run_benchmark())
    if args.compact:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
