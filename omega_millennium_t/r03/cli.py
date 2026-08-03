"""Command-line interface for Ω-PROBLEM-ATLAS-T∞ R0.3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .atlas import audit_output, compile_atlas
from .max_engine import compile_max_atlas
from .strict_audit import audit_max_output_strict


def _add_common_build_arguments(parser: argparse.ArgumentParser, *, max_mode: bool) -> None:
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-registry")
    parser.add_argument("--import-jsonl", action="append", default=[])
    if max_mode:
        parser.add_argument("--primary-budget", type=int, default=24)
        parser.add_argument("--secondary-budget", type=int, default=72)
        parser.add_argument("--experiment-budget", type=int, default=256)
    else:
        parser.add_argument("--primary-budget", type=int, default=6)
        parser.add_argument("--secondary-budget", type=int, default=24)
        parser.add_argument("--experiment-budget", type=int, default=64)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-atlas",
        description="Compile and audit OAK-safe problem, target and research-cell atlases.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="materialize the compact deterministic atlas")
    _add_common_build_arguments(build, max_mode=False)

    build_max = sub.add_parser(
        "build-max",
        help="materialize 12 targets per problem and 8 evidence work cells per target",
    )
    _add_common_build_arguments(build_max, max_mode=True)

    audit = sub.add_parser("audit", help="audit a compact materialized atlas")
    audit.add_argument("output_dir")

    audit_max = sub.add_parser(
        "audit-max",
        help="strictly audit receipts, graph references, cardinalities and MAX claims",
    )
    audit_max.add_argument("output_dir")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command in {"build", "build-max"}:
        kwargs = {
            "import_paths": args.import_jsonl,
            "primary_budget": args.primary_budget,
            "secondary_budget": args.secondary_budget,
            "experiment_budget": args.experiment_budget,
        }
        if args.source_registry:
            kwargs["source_registry"] = args.source_registry
        compiler = compile_max_atlas if args.command == "build-max" else compile_atlas
        result = compiler(Path(args.output_dir), **kwargs)
    elif args.command == "audit-max":
        result = audit_max_output_strict(Path(args.output_dir))
    else:
        result = audit_output(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
