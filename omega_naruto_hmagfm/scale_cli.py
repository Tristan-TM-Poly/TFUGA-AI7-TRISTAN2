"""CLI for million-scale Ω-NARUTO frontier experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .frontier_index import write_scale_index
from .frontier_scale import plan_scale_run, validate_scale_corpus, write_scale_corpus


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate, validate, and index deterministic compressed Ω-NARUTO "
            "frontier runs without a permanent total-record ceiling."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="print a deterministic partition plan")
    plan.add_argument("--target", type=int, required=True)
    plan.add_argument("--shard-records", type=int, default=25_000)
    plan.add_argument("--start-ordinal", type=int, default=0)

    generate = commands.add_parser("generate", help="write compressed resumable shards")
    generate.add_argument("--output-dir", type=Path, required=True)
    generate.add_argument("--target", type=int, required=True)
    generate.add_argument("--shard-records", type=int, default=25_000)
    generate.add_argument("--start-ordinal", type=int, default=0)
    generate.add_argument("--workers", type=int, default=1)
    generate.add_argument("--compression-level", type=int, default=6)
    generate.add_argument("--no-resume", action="store_true")

    validate = commands.add_parser("validate", help="stream-validate a scale corpus")
    validate.add_argument("--output-dir", type=Path, required=True)
    validate.add_argument("--report", type=Path)
    validate.add_argument("--max-findings", type=int, default=100)

    index = commands.add_parser("index", help="build streaming aggregates and M-minus telemetry")
    index.add_argument("--output-dir", type=Path, required=True)
    index.add_argument("--destination", type=Path)
    index.add_argument("--sample-limit", type=int, default=64)
    return parser


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "plan":
        _emit(
            plan_scale_run(
                target_records=args.target,
                shard_records=args.shard_records,
                start_ordinal=args.start_ordinal,
            ).to_dict()
        )
        return 0

    if args.command == "generate":
        manifest = write_scale_corpus(
            args.output_dir,
            target_records=args.target,
            shard_records=args.shard_records,
            start_ordinal=args.start_ordinal,
            workers=args.workers,
            compression_level=args.compression_level,
            resume=not args.no_resume,
        )
        _emit(manifest.to_dict())
        return 0 if manifest.complete else 2

    if args.command == "validate":
        report = validate_scale_corpus(
            args.output_dir,
            max_findings=args.max_findings,
        )
        rendered = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        print(rendered)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered + "\n", encoding="utf-8")
        return 0 if report.valid else 1

    index = write_scale_index(
        args.output_dir,
        destination=args.destination,
        sample_limit=args.sample_limit,
    )
    _emit(index.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
