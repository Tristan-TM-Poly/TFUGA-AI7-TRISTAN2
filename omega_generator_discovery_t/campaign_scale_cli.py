"""CLI for unbounded multi-epoch Ω-GENERATOR-DISCOVERY campaigns."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Sequence

from .campaign import load_campaign_spec
from .campaign_scale import (
    PROFILE_MULTIPLIERS,
    FrontierLedger,
    FrontierObservation,
    ScalePlanner,
    ScalePolicy,
    ValidationPolicy,
    decide_next_frontier,
    iter_epoch_bundles,
    resolve_target_records,
    validate_epoch_range,
    write_partition_matrix,
)
from .campaign_scale_emitter import ScalePartitionEmitter


def _target_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", choices=tuple(PROFILE_MULTIPLIERS))
    group.add_argument("--target-records", type=int)


def _scale_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-records-per-partition", type=int, default=250_000)
    parser.add_argument("--bundles-per-shard", type=int, default=2_048)
    parser.add_argument("--parallelism-hint", type=int, default=16)
    parser.add_argument("--validation-sample-ppm", type=int, default=10_000)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-generator-scale",
        description=(
            "Plan, emit, validate, and expand multi-epoch campaigns without a "
            "permanent total-addition ceiling."
        ),
    )
    parser.add_argument("--spec", help="Optional base campaign JSON specification.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser(
        "plan",
        help="Plan a million-to-billion or custom finite campaign.",
    )
    _target_args(plan)
    _scale_policy_args(plan)
    plan.add_argument("--output", help="Optional complete plan JSON path.")
    plan.add_argument("--matrix-output", help="Optional GitHub Actions matrix JSON path.")
    plan.add_argument("--summary-only", action="store_true")

    emit = sub.add_parser(
        "emit",
        help="Emit one global partition with atomic checkpoints.",
    )
    _target_args(emit)
    _scale_policy_args(emit)
    emit.add_argument("--global-partition-index", type=int, required=True)
    emit.add_argument("--output-dir", required=True)
    emit.add_argument("--resume", action="store_true")

    validate = sub.add_parser(
        "validate",
        help="Validate every bundle structurally and deeply validate risk/sample subsets.",
    )
    validate.add_argument("--epoch-index", type=int, default=0)
    validate.add_argument("--start", type=int, default=0)
    validate.add_argument("--generator-bundles", type=int, required=True)
    validate.add_argument("--sample-ppm", type=int, default=10_000)
    validate.add_argument("--output")

    digest = sub.add_parser(
        "digest",
        help="Stream and hash one epoch range without materialization.",
    )
    digest.add_argument("--epoch-index", type=int, default=0)
    digest.add_argument("--start", type=int, default=0)
    digest.add_argument("--generator-bundles", type=int, required=True)

    frontier = sub.add_parser(
        "frontier",
        help="Record an M+/M- observation and propose the next finite workload.",
    )
    frontier.add_argument("observation", help="JSON FrontierObservation file.")
    frontier.add_argument("--ledger", required=True)
    return parser


def _policy(args: argparse.Namespace) -> ScalePolicy:
    return ScalePolicy(
        target_records_per_partition=args.target_records_per_partition,
        bundles_per_shard=args.bundles_per_shard,
        parallelism_hint=args.parallelism_hint,
        validation_sample_ppm=args.validation_sample_ppm,
    )


def _planned(args: argparse.Namespace):
    spec = load_campaign_spec(args.spec)
    target = resolve_target_records(
        spec,
        profile=args.profile,
        target_records=args.target_records,
    )
    plan = ScalePlanner(spec, _policy(args)).plan(target)
    return spec, plan


def _render(payload: dict, output: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


def _plan(args: argparse.Namespace) -> int:
    spec, plan = _planned(args)
    if args.output:
        ScalePlanner(spec, _policy(args)).write(plan, args.output)
    if args.matrix_output:
        write_partition_matrix(plan, args.matrix_output)
    _render(plan.to_dict(include_partitions=not args.summary_only))
    return 0


def _emit(args: argparse.Namespace) -> int:
    spec, plan = _planned(args)
    if not 0 <= args.global_partition_index < plan.partition_count:
        raise ValueError("global-partition-index outside planned partition range")
    partition = plan.partitions[args.global_partition_index]
    report = ScalePartitionEmitter(
        spec,
        partition,
        args.output_dir,
        bundles_per_shard=args.bundles_per_shard,
    ).emit(resume=args.resume)
    _render(report.to_dict())
    return 0


def _validate(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    if args.generator_bundles < 0:
        raise ValueError("generator-bundles cannot be negative")
    stop = args.start + args.generator_bundles
    report = validate_epoch_range(
        spec,
        args.epoch_index,
        start=args.start,
        stop=stop,
        policy=ValidationPolicy(sample_ppm=args.sample_ppm),
    )
    _render(report.to_dict(), args.output)
    return 0 if report.status == "valid" else 3


def _digest(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    if args.generator_bundles < 0:
        raise ValueError("generator-bundles cannot be negative")
    stop = args.start + args.generator_bundles
    digest = hashlib.sha256()
    count = 0
    for record in iter_epoch_bundles(
        spec,
        args.epoch_index,
        start=args.start,
        stop=stop,
    ):
        line = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        digest.update(line.encode("utf-8"))
        count += 1
    _render(
        {
            "epoch_index": args.epoch_index,
            "generator_start": args.start,
            "generator_stop": stop,
            "generator_bundles": args.generator_bundles,
            "logical_records": count,
            "sha256": digest.hexdigest(),
            "no_permanent_total_addition_cap": True,
        }
    )
    return 0


def _frontier(args: argparse.Namespace) -> int:
    spec = load_campaign_spec(args.spec)
    raw = json.loads(Path(args.observation).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("observation must be a JSON object")
    observation = FrontierObservation.from_mapping(raw)
    decision = decide_next_frontier(
        observation,
        records_per_bundle=spec.records_per_bundle,
    )
    FrontierLedger(args.ledger).append(decision)
    _render(decision.to_dict())
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            return _plan(args)
        if args.command == "emit":
            return _emit(args)
        if args.command == "validate":
            return _validate(args)
        if args.command == "digest":
            return _digest(args)
        if args.command == "frontier":
            return _frontier(args)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"omega-generator-scale: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
