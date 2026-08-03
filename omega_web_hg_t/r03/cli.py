from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .compiler import audit_absorption, compile_absorption
from .search import SearchIndex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-web-hg-r03", description="Ω-WEB-HG-T∞ R0.3: absorption traçable, claims candidats, déduplication et recherche FTS.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Compiler un run R0.2 en corpus d'absorption interrogeable.")
    build.add_argument("run_dir")
    build.add_argument("--output-dir", required=True)
    query = sub.add_parser("query", help="Interroger un index R0.3 avec provenance.")
    query.add_argument("bundle_dir")
    query.add_argument("query")
    query.add_argument("--limit", type=int, default=20)
    query.add_argument("--kind", action="append", default=[])
    audit = sub.add_parser("audit", help="Auditer le corpus R0.3.")
    audit.add_argument("bundle_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            bundle = compile_absorption(args.run_dir, args.output_dir)
            print(json.dumps({"output_dir": args.output_dir, **bundle.report}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if bundle.report["status"] == "PASS_R0_3" else 1
        if args.command == "query":
            with SearchIndex(Path(args.bundle_dir) / "search.sqlite3") as index:
                results = index.query(args.query, limit=args.limit, kinds=tuple(args.kind))
            print(json.dumps({"query": args.query, "count": len(results), "results": results}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if args.command == "audit":
            result = audit_absorption(args.bundle_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS_R0_3" else 1
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"omega-web-hg-r03: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
