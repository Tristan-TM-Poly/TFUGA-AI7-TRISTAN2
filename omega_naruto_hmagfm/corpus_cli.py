"""CLI for large Ω-NARUTO corpus generation and validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .frontier import FrontierBudget, default_axes, write_corpus
from .frontier_validation import validate_frontier


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a finite, reproducible Ω-NARUTO corpus experiment without "
            "introducing a permanent total-record ceiling."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="stream a sharded JSONL corpus")
    generate.add_argument("--output-dir", type=Path, required=True)
    generate.add_argument(
        "--target",
        type=int,
        default=25_000,
        help="finite records for this run; not a permanent architecture maximum",
    )
    generate.add_argument("--shard-records", type=int, default=5_000)
    generate.add_argument("--resume", action="store_true")
    generate.add_argument(
        "--available-bytes",
        type=int,
        help="optional resource budget used when --target is omitted in API usage",
    )

    validate = subparsers.add_parser("validate", help="validate manifest and shards")
    validate.add_argument("--output-dir", type=Path, required=True)
    validate.add_argument("--report", type=Path)

    inspect = subparsers.add_parser("inspect", help="show seed-axis cardinality")
    inspect.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "generate":
        budget = FrontierBudget(
            requested_records=args.target,
            available_bytes=args.available_bytes,
        )
        manifest = write_corpus(
            args.output_dir,
            budget=budget,
            shard_records=args.shard_records,
            resume=args.resume,
        )
        print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if manifest.complete else 2

    if args.command == "validate":
        report = validate_frontier(args.output_dir)
        rendered = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        print(rendered)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered + "\n", encoding="utf-8")
        return 0 if report.valid else 1

    axes = default_axes()
    payload = {
        "schema": "omega_naruto_frontier.axes.v1",
        "axis_cardinality": axes.cardinality,
        "axes": {name: list(values) for name, values in axes.ordered_axes},
        "non_claim": (
            "Cardinality is combinatorial test capacity, not evidence, truth, "
            "or useful coverage by itself."
        ),
    }
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
