from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .gate import audit_promotion_gate, compile_promotion_gate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-promotion",
        description=(
            "Compile or audit a dry-run, fail-closed publication, novelty, prize and IP gate."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="compile a dry-run promotion bundle")
    compile_parser.add_argument("--bundle-json", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    compile_parser.add_argument(
        "--no-clean",
        action="store_true",
        help="do not remove an existing output directory before materialization",
    )

    audit_parser = sub.add_parser("audit", help="replay-audit one materialized gate")
    audit_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_promotion_gate(
            Path(args.bundle_json),
            Path(args.output_dir),
            clean=not args.no_clean,
        )
    else:
        result = audit_promotion_gate(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    if args.command == "audit":
        return 0 if result.get("valid") is True else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
