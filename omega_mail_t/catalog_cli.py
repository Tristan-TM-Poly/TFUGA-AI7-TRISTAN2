"""CLI for querying and auditing the Ω-MAIL-T R0.2 scenario atlas."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .catalog import DEFAULT_ROOT, audit, load_manifest, query_scenarios


def _emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-mail-catalog")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stats", help="Print atlas manifest statistics.")
    subparsers.add_parser("audit", help="Validate IDs, links, coverage, and safety flags.")

    query = subparsers.add_parser("query", help="Stream matching scenario templates.")
    query.add_argument("--company")
    query.add_argument("--intent")
    query.add_argument("--anomaly")
    query.add_argument("--locale")
    query.add_argument("--classification")
    query.add_argument("--limit", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "stats":
        _emit(load_manifest(args.root))
        return 0
    if args.command == "audit":
        report = audit(args.root)
        _emit(report)
        return 0 if report["valid"] else 1
    if args.command == "query":
        records = [
            asdict(record)
            for record in query_scenarios(
                root=args.root,
                company=args.company,
                intent=args.intent,
                anomaly=args.anomaly,
                locale=args.locale,
                classification=args.classification,
                limit=args.limit,
            )
        ]
        _emit(records)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
