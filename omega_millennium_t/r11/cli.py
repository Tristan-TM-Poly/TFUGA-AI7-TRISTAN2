from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .ledger import (
    audit_competition_ledger,
    compile_competition_ledger,
    recommend_active_cycles,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-competition-ledger",
        description="Compile, audit and read competition-cycle recommendations without external actions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="compile an immutable cycle ledger")
    compile_parser.add_argument("--bundle-json", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    compile_parser.add_argument("--no-clean", action="store_true")

    audit_parser = sub.add_parser("audit", help="replay-audit a compiled cycle ledger")
    audit_parser.add_argument("output_dir")

    recommend_parser = sub.add_parser(
        "recommend",
        help="read audited recommendations; does not register or submit",
    )
    recommend_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_competition_ledger(
            Path(args.bundle_json),
            Path(args.output_dir),
            clean=not args.no_clean,
        )
    elif args.command == "audit":
        result = audit_competition_ledger(Path(args.output_dir))
    else:
        result = recommend_active_cycles(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    if args.command == "audit":
        return 0 if result.get("valid") is True else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
