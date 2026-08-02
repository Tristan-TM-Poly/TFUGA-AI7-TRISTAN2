"""CLI for Ω-GENERATOR-DISCOVERY R0.5 virtual distributed frontiers."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Sequence

from .campaign import CampaignSpec
from .frontier_store import FrontierStore
from .frontier_virtual import (
    AdaptiveWaveScheduler,
    BaseCampaignShape,
    BudgetEnvelope,
    FRONTIER_PROFILES,
    MerkleMountainRange,
    PromotionEvidence,
    ResourceModel,
    VirtualFrontierPlan,
    VirtualFrontierPolicy,
    evaluate_promotion,
    resolve_frontier_target,
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _target_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", choices=tuple(FRONTIER_PROFILES))
    group.add_argument("--target-records", type=int)


def _policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-records-per-partition", type=int, default=250_000)
    parser.add_argument("--bundles-per-shard", type=int, default=2_048)
    parser.add_argument("--max-partitions-per-wave", type=int, default=256)
    parser.add_argument("--max-matrix-entries", type=int, default=256)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-generator-frontier",
        description=(
            "Plan, page, schedule and audit trillion-scale logical campaigns "
            "without materializing all epochs or partitions."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Create an O(1)-memory virtual plan.")
    _target_arguments(plan)
    _policy_arguments(plan)
    plan.add_argument("--output")
    plan.add_argument("--page-cursor", type=int)
    plan.add_argument("--page-limit", type=int, default=32)

    page = sub.add_parser("page", help="Address a partition page directly.")
    _target_arguments(page)
    _policy_arguments(page)
    page.add_argument("--cursor", type=int, default=0)
    page.add_argument("--limit", type=int, default=256)
    page.add_argument("--output")

    schedule = sub.add_parser("schedule", help="Fit the next wave to all budgets.")
    _target_arguments(schedule)
    _policy_arguments(schedule)
    schedule.add_argument("--cursor", type=int, default=0)
    schedule.add_argument("--max-records", type=int, required=True)
    schedule.add_argument("--max-bytes", type=int, required=True)
    schedule.add_argument("--max-seconds", type=float, required=True)
    schedule.add_argument("--max-cost-microunits", type=int, required=True)
    schedule.add_argument("--max-api-calls", type=int, required=True)
    schedule.add_argument("--max-files", type=int, required=True)
    schedule.add_argument("--max-commits", type=int, required=True)
    schedule.add_argument("--bytes-per-record", type=int, default=640)
    schedule.add_argument("--nanoseconds-per-record", type=int, default=25_000)
    schedule.add_argument("--cost-microunits-per-record", type=int, default=1)
    schedule.add_argument("--records-per-api-call", type=int, default=10_000)
    schedule.add_argument("--records-per-file", type=int, default=100_000)
    schedule.add_argument("--records-per-commit", type=int, default=2_000_000)
    schedule.add_argument("--output")

    mmr = sub.add_parser("mmr-demo", help="Build a deterministic streaming MMR receipt.")
    mmr.add_argument("--leaves", type=int, default=100_000)
    mmr.add_argument("--namespace", default="omega-frontier-demo")

    db_init = sub.add_parser("db-init", help="Initialize the R0.5 SQLite control plane.")
    db_init.add_argument("--db", required=True)

    db_seed = sub.add_parser("db-seed", help="Seed one virtual partition page.")
    db_seed.add_argument("--db", required=True)
    _target_arguments(db_seed)
    _policy_arguments(db_seed)
    db_seed.add_argument("--cursor", type=int, default=0)
    db_seed.add_argument("--limit", type=int, default=256)

    db_claim = sub.add_parser("db-claim", help="Atomically claim one pending partition.")
    db_claim.add_argument("--db", required=True)
    db_claim.add_argument("--plan-fingerprint", required=True)
    db_claim.add_argument("--worker-id", required=True)
    db_claim.add_argument("--ttl-seconds", type=int, default=3_600)

    db_status = sub.add_parser("db-status", help="Summarize one plan in the control plane.")
    db_status.add_argument("--db", required=True)
    db_status.add_argument("--plan-fingerprint", required=True)
    db_status.add_argument("--audit", action="store_true")

    oak = sub.add_parser("oak", help="Evaluate an OAK promotion request.")
    oak.add_argument(
        "--level",
        choices=("candidate", "validated_synthetic", "empirical", "canon"),
        required=True,
    )
    for field in asdict(PromotionEvidence()):
        oak.add_argument(f"--{field.replace('_', '-')}", action="store_true")
    return parser


def _policy(args: argparse.Namespace) -> VirtualFrontierPolicy:
    return VirtualFrontierPolicy(
        target_records_per_partition=args.target_records_per_partition,
        bundles_per_shard=args.bundles_per_shard,
        max_partitions_per_wave=args.max_partitions_per_wave,
        max_matrix_entries=args.max_matrix_entries,
    )


def _plan(args: argparse.Namespace) -> VirtualFrontierPlan:
    shape = BaseCampaignShape.from_campaign_spec(CampaignSpec())
    target = resolve_frontier_target(
        profile=getattr(args, "profile", None),
        target_records=getattr(args, "target_records", None),
    )
    return VirtualFrontierPlan.build(shape, target, _policy(args))


def _write(payload: object, output: str | None = None) -> None:
    rendered = _json(payload)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def _run(args: argparse.Namespace) -> int:
    if args.command == "plan":
        plan = _plan(args)
        payload = plan.to_dict()
        if args.page_cursor is not None:
            payload["partition_page"] = plan.partition_page(
                args.page_cursor, args.page_limit
            )
        _write(payload, args.output)
        return 0
    if args.command == "page":
        plan = _plan(args)
        _write(plan.partition_page(args.cursor, args.limit), args.output)
        return 0
    if args.command == "schedule":
        plan = _plan(args)
        model = ResourceModel(
            bytes_per_record=args.bytes_per_record,
            nanoseconds_per_record=args.nanoseconds_per_record,
            cost_microunits_per_record=args.cost_microunits_per_record,
            records_per_api_call=args.records_per_api_call,
            records_per_file=args.records_per_file,
            records_per_commit=args.records_per_commit,
        )
        budget = BudgetEnvelope(
            max_logical_records=args.max_records,
            max_bytes_written=args.max_bytes,
            max_nanoseconds=max(1, int(args.max_seconds * 1_000_000_000)),
            max_cost_microunits=args.max_cost_microunits,
            max_api_calls=args.max_api_calls,
            max_files=args.max_files,
            max_commits=args.max_commits,
        )
        wave = AdaptiveWaveScheduler(
            model=model,
            max_partitions_per_wave=plan.policy.max_partitions_per_wave,
        ).schedule(plan, args.cursor, budget)
        _write(wave.to_dict(), args.output)
        return 0
    if args.command == "mmr-demo":
        if args.leaves < 0:
            raise ValueError("leaves cannot be negative")
        mmr = MerkleMountainRange()
        for index in range(args.leaves):
            mmr.append(
                {
                    "namespace": args.namespace,
                    "index": index,
                    "id": f"R0.5-{index:018d}",
                }
            )
        _write(
            {
                **mmr.receipt(),
                "namespace": args.namespace,
                "oak_boundary": "Merkle integrity is not empirical validation.",
            }
        )
        return 0
    if args.command == "db-init":
        store = FrontierStore(args.db)
        _write({"status": "initialized", "db": str(store.path)})
        return 0
    if args.command == "db-seed":
        plan = _plan(args)
        store = FrontierStore(args.db)
        seeded = store.seed_partition_page(plan, cursor=args.cursor, limit=args.limit)
        _write(
            {
                "status": "seeded",
                "db": str(store.path),
                "plan_fingerprint": plan.plan_fingerprint,
                "seeded_partitions": seeded,
                "control_plane_status": store.status(plan.plan_fingerprint),
            }
        )
        return 0
    if args.command == "db-claim":
        store = FrontierStore(args.db)
        claim = store.claim(
            args.plan_fingerprint,
            args.worker_id,
            ttl_seconds=args.ttl_seconds,
        )
        _write({"status": "claimed" if claim else "empty", "claim": claim})
        return 0
    if args.command == "db-status":
        store = FrontierStore(args.db)
        payload = store.status(args.plan_fingerprint)
        if args.audit:
            payload["integrity_audit"] = store.integrity_audit(args.plan_fingerprint)
        _write(payload)
        return 0
    if args.command == "oak":
        evidence = PromotionEvidence(
            **{
                field: bool(getattr(args, field))
                for field in asdict(PromotionEvidence())
            }
        )
        _write(evaluate_promotion(args.level, evidence).to_dict())
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"omega-generator-frontier: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
