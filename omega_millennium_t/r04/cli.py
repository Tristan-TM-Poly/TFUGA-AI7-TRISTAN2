"""CLI for Ω-PROBLEM-ATLAS-T∞ R0.4 source adapters."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .source_adapters import compile_source_bundle
from .strict_audit import audit_source_bundle_strict


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-sources",
        description=(
            "Compile revision-pinned offline source snapshots into OAK-safe "
            "Problem Atlas imports and dated status receipts."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser(
        "compile",
        help="compile one or more source snapshot JSON files",
    )
    compile_parser.add_argument("--snapshot", action="append", required=True)
    compile_parser.add_argument("--output-dir", required=True)

    audit_parser = sub.add_parser(
        "audit",
        help="strictly audit receipts, counts, claims and artifact integrity",
    )
    audit_parser.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_source_bundle(
            tuple(Path(path) for path in args.snapshot),
            Path(args.output_dir),
        )
    else:
        result = audit_source_bundle_strict(Path(args.output_dir))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
