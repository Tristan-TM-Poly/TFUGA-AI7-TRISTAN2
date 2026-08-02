"""Command line interface for Ω-ORG-FAM-T."""
from __future__ import annotations

import argparse
import json
from itertools import islice
from pathlib import Path
from typing import Sequence

from .atlas import audit_atlas, compile_atlas
from .classifier import classify_features
from .family_space import iter_requested_cells


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-organic-family")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="stream a deterministic family-space atlas")
    generate.add_argument("--output-dir", default="generated/omega_org_fam_t_r01")
    generate.add_argument("--family-records", type=int, default=262_144)
    generate.add_argument("--family-shard-size", type=int, default=16_384)
    generate.add_argument("--evidence-shard-size", type=int, default=32_768)

    classify = sub.add_parser("classify", help="rank candidate family cells from explicit features")
    classify.add_argument("features", nargs="*")
    classify.add_argument("--scan", type=int, default=262_144)
    classify.add_argument("--top-k", type=int, default=20)

    audit = sub.add_parser("audit", help="verify compressed shard hashes")
    audit.add_argument("output_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        manifest = compile_atlas(
            Path(args.output_dir),
            family_records=args.family_records,
            family_shard_size=args.family_shard_size,
            evidence_shard_size=args.evidence_shard_size,
        )
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    if args.command == "classify":
        cells = islice(iter_requested_cells(args.scan), args.scan)
        result = classify_features(cells, set(args.features), top_k=args.top_k)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "audit":
        report = audit_atlas(Path(args.output_dir))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["valid"] else 2
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
