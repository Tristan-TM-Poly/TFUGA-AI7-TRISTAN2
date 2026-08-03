"""Command-line interface for Ω-PROBLEM-ATLAS-T∞ R0.3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .atlas import audit_output, compile_atlas


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-atlas",
        description="Compile and audit an OAK-safe atlas of problem families and research cells.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="materialize a deterministic atlas")
    build.add_argument("--output-dir", required=True)
    build.add_argument("--source-registry")
    build.add_argument("--import-jsonl", action="append", default=[])
    build.add_argument("--primary-budget", type=int, default=6)
    build.add_argument("--secondary-budget", type=int, default=24)
    build.add_argument("--experiment-budget", type=int, default=64)

    audit = sub.add_parser("audit", help="audit a materialized atlas")
    audit.add_argument("output_dir")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        kwargs = {
            "import_paths": args.import_jsonl,
            "primary_budget": args.primary_budget,
            "secondary_budget": args.secondary_budget,
            "experiment_budget": args.experiment_budget,
        }
        if args.source_registry:
            kwargs["source_registry"] = args.source_registry
        result = compile_atlas(Path(args.output_dir), **kwargs)
    else:
        result = audit_output(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
