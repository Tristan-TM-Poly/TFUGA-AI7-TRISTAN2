"""CLI for querying and auditing the R0.2 massive atlas."""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from .catalog import audit_catalog, catalog_statistics, query_generators


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-generator-catalog")
    parser.add_argument("--root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stats")
    sub.add_parser("audit")
    query = sub.add_parser("query")
    query.add_argument("--domain")
    query.add_argument("--family")
    query.add_argument("--scale")
    query.add_argument("--status")
    query.add_argument("--limit", type=int, default=100)
    args = parser.parse_args(argv)
    if args.command == "stats":
        result = catalog_statistics(args.root)
    elif args.command == "audit":
        result = audit_catalog(args.root).to_dict()
    else:
        result = [record.to_dict() for record in query_generators(
            domain=args.domain,
            family=args.family,
            scale=args.scale,
            status=args.status,
            limit=args.limit,
            root=args.root,
        )]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
