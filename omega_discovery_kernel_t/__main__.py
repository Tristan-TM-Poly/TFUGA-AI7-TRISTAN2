"""CLI for Ω-DISCOVERY-KERNEL-T∞.

Examples:
    python -m omega_discovery_kernel_t demo --output-dir generated/discovery-kernel
    python -m omega_discovery_kernel_t audit path/to/events.jsonl
    python -m omega_discovery_kernel_t catalog --output event-catalog.json
    python -m omega_discovery_kernel_t frontier --events 50000 --output-dir generated/frontier-50k
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .catalog import catalog_manifest
from .demo import build_raman_closed_loop
from .kernel import DiscoveryLedger
from .streaming import (
    AdaptiveFrontierConfig,
    FrontierExperimentConfig,
    run_frontier_experiment,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m omega_discovery_kernel_t",
        description="Compile, audit, and scale OAK-safe closed-loop discovery event ledgers.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate the deterministic Raman closed-loop example.")
    demo.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/raman-r0-2")

    audit = sub.add_parser("audit", help="Audit an existing events.jsonl in-memory ledger.")
    audit.add_argument("events_jsonl")
    audit.add_argument("--output-dir", default=None)

    catalog = sub.add_parser("catalog", help="Emit the 64-event canonical contract catalog.")
    catalog.add_argument("--output", default=None)

    frontier = sub.add_parser(
        "frontier",
        help="Run a finite adaptive frontier experiment without imposing a permanent total-event ceiling.",
    )
    frontier.add_argument("--events", type=int, default=50_000)
    frontier.add_argument("--namespaces", type=int, default=16)
    frontier.add_argument("--seed", type=int, default=7)
    frontier.add_argument("--failure-period", type=int, default=1)
    frontier.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/frontier-50k-r0-2")
    frontier.add_argument("--initial-shard-bytes", type=int, default=262_144)
    frontier.add_argument("--shard-growth-factor", type=float, default=2.0)
    frontier.add_argument("--checkpoint-interval", type=int, default=1_000)
    frontier.add_argument("--commit-interval", type=int, default=1_000)
    frontier.add_argument("--minimum-free-bytes", type=int, default=64 * 1024 * 1024)
    frontier.add_argument("--resume", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "demo":
        ledger = build_raman_closed_loop()
        output = ledger.write(args.output_dir)
        print(json.dumps({"output_dir": str(output), **ledger.audit().to_dict()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "audit":
        ledger = DiscoveryLedger.read_jsonl(args.events_jsonl)
        audit = ledger.audit()
        if args.output_dir:
            ledger.write(args.output_dir)
        print(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2))
        return 0 if not any(item.severity == "P0" for item in audit.findings) else 1
    if args.command == "catalog":
        value = catalog_manifest()
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(json.dumps({"output": str(target), "event_type_count": value["event_type_count"]}, indent=2))
        else:
            print(text, end="")
        return 0
    if args.command == "frontier":
        experiment = FrontierExperimentConfig(
            target_events=args.events,
            namespace_count=args.namespaces,
            seed=args.seed,
            failure_period=args.failure_period,
        )
        ledger_config = AdaptiveFrontierConfig(
            initial_shard_bytes=args.initial_shard_bytes,
            shard_growth_factor=args.shard_growth_factor,
            checkpoint_interval=args.checkpoint_interval,
            commit_interval=args.commit_interval,
            minimum_free_bytes=args.minimum_free_bytes,
        )
        summary = run_frontier_experiment(
            args.output_dir,
            experiment=experiment,
            ledger_config=ledger_config,
            resume=args.resume,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        findings = summary["manifest"].get("integrity_findings", [])
        return 0 if not findings else 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
