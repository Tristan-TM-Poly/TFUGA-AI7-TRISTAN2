"""Command-line interface for Ω-POLYGLOT-MULTIVERSE-T∞ R0.2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .campaign import materialize
from .catalog import generate_catalog
from .frontier import LogicalFrontier
from .generator import generate_affine_source, write_artifact
from .hardware import fingerprint
from .seed import materialize_seed_atlas


def _frontier(count: int) -> LogicalFrontier:
    specs = generate_catalog(count)
    return LogicalFrontier(tuple(spec.algorithm_id for spec in specs))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-polyglot-r02")
    commands = parser.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--count", type=int, default=1024)
    catalog.add_argument("--output", type=Path)
    frontier = commands.add_parser("frontier")
    frontier.add_argument("--algorithms", type=int, default=1024)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("index", type=int)
    inspect.add_argument("--algorithms", type=int, default=1024)
    campaign = commands.add_parser("materialize")
    campaign.add_argument("--algorithms", type=int, default=1024)
    campaign.add_argument("--start", type=int, default=0)
    campaign.add_argument("--count", type=int, required=True)
    campaign.add_argument("--shard-size", type=int, default=2048)
    campaign.add_argument("--output-dir", type=Path, required=True)
    campaign.add_argument("--resume", action="store_true")
    generate = commands.add_parser("generate-affine")
    generate.add_argument("--language", choices=("python", "c", "cpp", "rust"), required=True)
    generate.add_argument("--strategy", default="scalar")
    generate.add_argument("--output-dir", type=Path, required=True)
    seed = commands.add_parser("seed")
    seed.add_argument("--algorithms", type=int, default=1024)
    seed.add_argument("--shard-size", type=int, default=4096)
    seed.add_argument("--output-dir", type=Path, required=True)
    commands.add_parser("hardware")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        payload = [spec.to_dict() | {"digest": spec.digest} for spec in generate_catalog(args.count)]
        text = json.dumps({"count": len(payload), "items": payload}, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.command == "frontier":
        frontier = _frontier(args.algorithms)
        print(json.dumps({
            "algorithms": len(frontier.algorithm_ids),
            "variants_per_algorithm": frontier.axes.variants_per_algorithm,
            "logical_frontier_size": frontier.size,
            "permanent_total_cap": None,
            "status": "LOGICAL_NOT_MATERIALIZED",
        }, indent=2, sort_keys=True))
        return 0
    if args.command == "inspect":
        frontier = _frontier(args.algorithms)
        variant = frontier.address_at(args.index)
        print(json.dumps({
            "index": args.index,
            "variant_id": variant.variant_id,
            "uri": variant.uri,
            "variant": variant.to_dict(),
        }, indent=2, sort_keys=True))
        return 0
    if args.command == "materialize":
        frontier = _frontier(args.algorithms)
        manifest = materialize(
            frontier, args.output_dir, start_index=args.start, count=args.count,
            shard_size=args.shard_size, resume=args.resume,
        )
        print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.command == "generate-affine":
        artifact = generate_affine_source(args.language, args.strategy)
        path = write_artifact(args.output_dir, artifact)
        print(json.dumps({
            "path": str(path), "sha256": artifact.sha256, "generator": artifact.generator_version,
        }, indent=2, sort_keys=True))
        return 0
    if args.command == "seed":
        manifest = materialize_seed_atlas(
            args.output_dir, algorithms=args.algorithms, shard_size=args.shard_size,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.command == "hardware":
        print(json.dumps(fingerprint().to_dict(), indent=2, sort_keys=True))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
