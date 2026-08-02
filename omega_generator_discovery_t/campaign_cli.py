"""CLI for million-record Ω-GENERATOR-DISCOVERY campaigns."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .campaign import (
    CampaignEmitter,
    iter_generator_bundles,
    load_campaign_spec,
    partition_campaign,
    stream_digest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-generator-campaign",
        description=(
            "Plan, stream, partition and checkpoint generator-discovery campaigns "
            "without a permanent total-addition cap."
        ),
    )
    parser.add_argument("--spec", help="Optional JSON campaign specification.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Print campaign cardinality and balanced partitions.")
    plan.add_argument("--partition-count", type=int, default=64)
    plan.add_argument("--output", help="Optional JSON manifest output path.")
    plan.add_argument("--include-partitions", action="store_true")

    emit = sub.add_parser("emit", help="Emit one resumable partition as planner-ready JSONL shards.")
    emit.add_argument("--partition-count", type=int, default=64)
    emit.add_argument("--partition-index", type=int, required=True)
    emit.add_argument("--bundles-per-shard", type=int, default=2_048)
    emit.add_argument("--output-dir", required=True)
    emit.add_argument("--resume", action="store_true")

    stress = sub.add_parser("stress", help="Stream and hash a finite number of generator bundles.")
    stress.add_argument("--generator-bundles", type=int, default=16_384)
    stress.add_argument("--start", type=int, default=0)
    return parser


def _plan(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    partitions = partition_campaign(spec, args.partition_count)
    payload = spec.manifest()
    payload["partition_count"] = args.partition_count
    payload["partition_generator_bundles_min"] = min(p.generator_bundles for p in partitions)
    payload["partition_generator_bundles_max"] = max(p.generator_bundles for p in partitions)
    payload["partition_logical_records_min"] = min(p.logical_records for p in partitions)
    payload["partition_logical_records_max"] = max(p.logical_records for p in partitions)
    if args.include_partitions:
        payload["partitions"] = [partition.to_dict() for partition in partitions]
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


def _emit(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    partitions = partition_campaign(spec, args.partition_count)
    if not 0 <= args.partition_index < len(partitions):
        raise ValueError("partition-index outside partition range")
    emitter = CampaignEmitter(
        spec,
        partitions[args.partition_index],
        args.output_dir,
        bundles_per_shard=args.bundles_per_shard,
    )
    report = emitter.emit(resume=args.resume)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _stress(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    if args.generator_bundles < 0:
        raise ValueError("generator-bundles cannot be negative")
    stop = args.start + args.generator_bundles
    count, digest = stream_digest(
        iter_generator_bundles(spec, start=args.start, stop=stop)
    )
    payload = {
        "campaign_id": spec.campaign_id,
        "campaign_fingerprint": spec.fingerprint,
        "generator_start": args.start,
        "generator_stop": stop,
        "generator_bundles": args.generator_bundles,
        "logical_records_streamed": count,
        "expected_logical_records": args.generator_bundles * spec.records_per_bundle,
        "sha256": digest,
        "no_permanent_total_addition_cap": True,
        "oak_boundary": "Streaming volume is not scientific validation.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            return _plan(args)
        if args.command == "emit":
            return _emit(args)
        if args.command == "stress":
            return _stress(args)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"omega-generator-campaign: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
