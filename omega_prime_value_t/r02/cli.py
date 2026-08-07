from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import deterministic_benchmark
from .engine import CampaignEngine
from .ntt_kernel import validate_convolution
from .planner import CampaignPlanner, PlannerPolicy, verify_manifest
from .portfolio import PortfolioAllocator
from .registry import LocalPrimeRegistry
from .storage import CampaignStore


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _policy(args: argparse.Namespace) -> PlannerPolicy:
    return PlannerPolicy(
        exponent_min=args.exponent_min,
        exponent_max=args.exponent_max,
        k_min=args.k_min,
        k_max=args.k_max,
        shard_size=args.shard_size,
        max_value=args.max_value,
    )


def command_plan(args: argparse.Namespace) -> int:
    manifest = CampaignPlanner(_policy(args)).build()
    _write(manifest.to_dict(), args.output)
    return 0


def command_run(args: argparse.Namespace) -> int:
    manifest = CampaignPlanner(_policy(args)).build()
    with CampaignStore(args.database) as store:
        summary = CampaignEngine(store, sieve_bound=args.sieve_bound).execute(
            manifest, max_tasks=args.max_tasks
        )
        payload = {
            "manifest": manifest.to_dict(),
            "manifest_verified": verify_manifest(manifest),
            "summary": summary.to_dict(),
            "database_integrity": store.integrity_check(),
            "registry_count": LocalPrimeRegistry(store).count(),
        }
    _write(payload, args.output)
    return 0


def command_status(args: argparse.Namespace) -> int:
    with CampaignStore(args.database) as store:
        payload = {
            "checkpoint": store.checkpoint(args.campaign_id),
            "integrity": store.integrity_check(),
            "events": store.event_count(args.campaign_id),
            "registry": LocalPrimeRegistry(store).export(),
        }
    _write(payload, args.output)
    return 0


def _parse_vector(text: str) -> list[int]:
    if not text.strip():
        return []
    return [int(piece.strip()) for piece in text.split(",")]


def command_convolve(args: argparse.Namespace) -> int:
    payload = validate_convolution(_parse_vector(args.left), _parse_vector(args.right), args.modulus)
    _write(payload, args.output)
    return 0 if payload["matches_naive"] else 1


def command_portfolio(args: argparse.Namespace) -> int:
    allocator = PortfolioAllocator(exploration=args.exploration)
    observations = json.loads(Path(args.observations).read_text(encoding="utf-8"))
    if not isinstance(observations, list):
        raise ValueError("observations JSON must be a list")
    for observation in observations:
        allocator.observe(
            str(observation["arm"]),
            float(observation["reward"]),
            float(observation.get("compute_units", 1.0)),
        )
    _write(allocator.report(), args.output)
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    _write(deterministic_benchmark(), args.output)
    return 0


def _add_policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--exponent-min", type=int, default=8)
    parser.add_argument("--exponent-max", type=int, default=12)
    parser.add_argument("--k-min", type=int, default=1)
    parser.add_argument("--k-max", type=int, default=999)
    parser.add_argument("--shard-size", type=int, default=256)
    parser.add_argument("--max-value", type=int, default=2**64 - 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-prime-value-r02",
        description="Resumable OAK-safe public prime campaigns and NTT assets",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    _add_policy_arguments(plan)
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    run = sub.add_parser("run")
    _add_policy_arguments(run)
    run.add_argument("--database", required=True)
    run.add_argument("--sieve-bound", type=int, default=10_000)
    run.add_argument("--max-tasks", type=int)
    run.add_argument("--output")
    run.set_defaults(func=command_run)

    status = sub.add_parser("status")
    status.add_argument("--database", required=True)
    status.add_argument("--campaign-id", required=True)
    status.add_argument("--output")
    status.set_defaults(func=command_status)

    convolve = sub.add_parser("convolve")
    convolve.add_argument("--left", required=True, help="comma-separated integers")
    convolve.add_argument("--right", required=True, help="comma-separated integers")
    convolve.add_argument("--modulus", type=int, default=998244353)
    convolve.add_argument("--output")
    convolve.set_defaults(func=command_convolve)

    portfolio = sub.add_parser("portfolio")
    portfolio.add_argument("--observations", required=True)
    portfolio.add_argument("--exploration", type=float, default=2**0.5)
    portfolio.add_argument("--output")
    portfolio.set_defaults(func=command_portfolio)

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--output")
    benchmark.set_defaults(func=command_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
