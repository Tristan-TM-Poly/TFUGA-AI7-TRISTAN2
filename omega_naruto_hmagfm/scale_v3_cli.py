"""CLI for Ω-NARUTO Frontier Scale v3 parallel proofs and ledgers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .frontier_ledger import write_run_ledger
from .frontier_parallel import write_parallel_index, write_parallel_validation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run parallel frontier proofs and federate immutable manifests."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "parallel-validate",
        help="recompute all records and shard hashes in parallel",
    )
    validate.add_argument("--output-dir", type=Path, required=True)
    validate.add_argument("--destination", type=Path, required=True)
    validate.add_argument("--workers", type=int, default=4)

    index = commands.add_parser(
        "parallel-index",
        help="build exact shard-parallel aggregate index",
    )
    index.add_argument("--output-dir", type=Path, required=True)
    index.add_argument("--destination", type=Path, required=True)
    index.add_argument("--workers", type=int, default=4)
    index.add_argument("--sample-limit", type=int, default=128)

    ledger = commands.add_parser(
        "ledger",
        help="federate one or more immutable scale manifests",
    )
    ledger.add_argument("--manifest", type=Path, action="append", required=True)
    ledger.add_argument("--destination", type=Path, required=True)
    ledger.add_argument("--allow-gaps", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "parallel-validate":
        report = write_parallel_validation(
            args.output_dir,
            destination=args.destination,
            workers=args.workers,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report.valid else 1

    if args.command == "parallel-index":
        index = write_parallel_index(
            args.output_dir,
            destination=args.destination,
            workers=args.workers,
            sample_limit=args.sample_limit,
        )
        print(json.dumps(index.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    ledger = write_run_ledger(
        args.manifest,
        destination=args.destination,
        require_contiguous=not args.allow_gaps,
    )
    print(json.dumps(ledger.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if ledger.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
