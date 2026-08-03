from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .routing import audit_routing_campaign, compile_routing_campaign


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-routing",
        description="Compile and audit evidence-updated, diversity-constrained research routing.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="replay an event ledger and build a portfolio")
    compile_parser.add_argument("--cells-jsonl", required=True)
    compile_parser.add_argument("--events-json", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    compile_parser.add_argument("--budget", type=int, default=24)
    compile_parser.add_argument("--max-per-problem", type=int, default=2)

    audit_parser = sub.add_parser("audit", help="strictly replay-audit a routing campaign")
    audit_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_routing_campaign(
            Path(args.cells_jsonl),
            Path(args.events_json),
            Path(args.output_dir),
            budget=args.budget,
            max_per_problem=args.max_per_problem,
        )
    else:
        result = audit_routing_campaign(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
