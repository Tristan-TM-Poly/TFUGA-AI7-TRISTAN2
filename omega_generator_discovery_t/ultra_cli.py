"""CLI for Ω-GENERATOR-DISCOVERY R0.3 Ultra."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .ultra_catalog import (
    DEFAULT_ROOT,
    audit_ultra_catalog,
    catalog_statistics,
    deterministic_validation_sample,
    export_subatlas,
    get_generator,
    query_generators,
    related_bundle,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-generator-ultra",
        description="Query and audit the OAK-safe R0.3 Ultra candidate atlas.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("stats")
    commands.add_parser("audit")

    query = commands.add_parser("query")
    query.add_argument("--domain")
    query.add_argument("--family")
    query.add_argument("--scale")
    query.add_argument("--representation")
    query.add_argument("--regime")
    query.add_argument("--status")
    query.add_argument("--invariant")
    query.add_argument("--risk-tier", choices=("low", "medium", "high"))
    query.add_argument("--supports-inverse", choices=("yes", "no"))
    query.add_argument("--limit", type=int, default=20)
    query.add_argument("--offset", type=int, default=0)

    get = commands.add_parser("get")
    get.add_argument("generator_id")

    bundle = commands.add_parser("bundle")
    bundle.add_argument("generator_id")

    sample = commands.add_parser("sample")
    sample.add_argument("--modulus", type=int, default=16)
    sample.add_argument("--residue", type=int, default=0)
    sample.add_argument("--exclude-high-risk", action="store_true")
    sample.add_argument("--limit", type=int, default=100)

    export = commands.add_parser("export")
    export.add_argument("output", type=Path)
    export.add_argument("--domain")
    export.add_argument("--family")
    export.add_argument("--limit", type=int, default=1000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root: Path = args.root
    if args.command == "stats":
        result = catalog_statistics(root)
    elif args.command == "audit":
        result = audit_ultra_catalog(root).to_dict()
    elif args.command == "query":
        inverse = None
        if args.supports_inverse == "yes":
            inverse = True
        elif args.supports_inverse == "no":
            inverse = False
        result = [
            record.to_dict()
            for record in query_generators(
                root=root,
                domain=args.domain,
                family=args.family,
                scale=args.scale,
                representation=args.representation,
                regime=args.regime,
                status=args.status,
                invariant=args.invariant,
                risk_tier=args.risk_tier,
                supports_inverse=inverse,
                limit=args.limit,
                offset=args.offset,
            )
        ]
    elif args.command == "get":
        result = get_generator(args.generator_id, root).to_dict()
    elif args.command == "bundle":
        result = related_bundle(args.generator_id, root)
    elif args.command == "sample":
        selected = deterministic_validation_sample(
            root=root,
            modulus=args.modulus,
            residue=args.residue,
            include_all_high_risk=not args.exclude_high_risk,
        )
        result = {
            "count": len(selected),
            "generator_ids": list(selected[: args.limit]),
            "truncated": len(selected) > args.limit,
            "mode": "high_risk_exhaustive_plus_deterministic_sample"
            if not args.exclude_high_risk else "deterministic_sample_only",
        }
    else:
        result = export_subatlas(
            args.output,
            root=root,
            domain=args.domain,
            family=args.family,
            limit=args.limit,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
