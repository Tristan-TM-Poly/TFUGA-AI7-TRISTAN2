"""CLI for Ω-DISCOVERY-KERNEL-T∞.

Examples:
    python -m omega_discovery_kernel_t demo --output-dir generated/discovery-kernel
    python -m omega_discovery_kernel_t audit path/to/events.jsonl
    python -m omega_discovery_kernel_t catalog --output event-catalog.json
    python -m omega_discovery_kernel_t frontier --events 50000 --output-dir generated/frontier-50k
    python -m omega_discovery_kernel_t million-frontier --output-dir generated/frontier-1m
    python -m omega_discovery_kernel_t plan-additions --output-dir generated/additions-50100
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .catalog_r03 import catalog_manifest
from .demo import build_raman_closed_loop
from .factory import KnowledgeFrontierTargets, plan_knowledge_frontier
from .kernel import DiscoveryLedger
from .million_frontier import MillionFrontierConfig
from .million_optimized import run_forced_resume_million_frontier
from .streaming import AdaptiveFrontierConfig, FrontierExperimentConfig, run_frontier_experiment


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m omega_discovery_kernel_t",
        description="Compile, audit, scale, and plan OAK-safe discovery frontiers.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate the deterministic Raman closed-loop example.")
    demo.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/raman-r0-2")

    audit = sub.add_parser("audit", help="Audit an existing events.jsonl in-memory ledger.")
    audit.add_argument("events_jsonl")
    audit.add_argument("--output-dir", default=None)

    catalog = sub.add_parser("catalog", help="Emit the corrected 64-event canonical contract catalog.")
    catalog.add_argument("--output", default=None)

    frontier = sub.add_parser(
        "frontier",
        help="Run a finite adaptive event experiment without imposing a permanent total-event ceiling.",
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

    million = sub.add_parser(
        "million-frontier",
        help="Force an interruption and exact resume across a finite million-event OAKBench frontier.",
    )
    million.add_argument("--events", type=int, default=1_000_000)
    million.add_argument("--interrupt-after", type=int, default=524_288)
    million.add_argument("--namespaces", type=int, default=256)
    million.add_argument("--seed", type=int, default=73)
    million.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/frontier-1m-r0-3")
    million.add_argument("--initial-shard-bytes", type=int, default=4 * 1024 * 1024)
    million.add_argument("--shard-growth-factor", type=float, default=1.6)
    million.add_argument("--checkpoint-interval", type=int, default=50_000)
    million.add_argument("--sqlite-batch-size", type=int, default=10_000)
    million.add_argument("--minimum-free-bytes", type=int, default=512 * 1024 * 1024)
    million.add_argument("--latency-saturation-seconds", type=float, default=8.0)
    million.add_argument("--rss-saturation-bytes", type=int, default=2 * 1024 * 1024 * 1024)

    plan = sub.add_parser(
        "plan-additions",
        help="Compile a reversible Ω-SANS-PLAFOND GitHub dry-run plan from diversified logical additions.",
    )
    plan.add_argument("--output-dir", default="generated/omega_discovery_kernel_t/additions-50100-r0-2")
    plan.add_argument("--cells", type=int, default=100)
    plan.add_argument("--claims-per-cell", type=int, default=10)
    plan.add_argument("--evidence-per-claim", type=int, default=5)
    plan.add_argument("--experiments-per-claim", type=int, default=1)
    plan.add_argument("--results-per-experiment", type=int, default=10)
    plan.add_argument("--actions-per-result", type=int, default=1)
    plan.add_argument("--memory-rules-per-result", type=int, default=1)
    plan.add_argument("--identities-per-claim", type=int, default=1)
    plan.add_argument("--benchmark-cases", type=int, default=12_000)
    plan.add_argument("--initial-shard-bytes", type=int, default=262_144)
    plan.add_argument("--shard-growth-factor", type=float, default=2.0)
    plan.add_argument("--proposed-branch", default="feat/omega-discovery-frontier-generated")
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
        return 0 if not summary["manifest"].get("integrity_findings") else 1
    if args.command == "million-frontier":
        config = MillionFrontierConfig(
            target_events=args.events,
            forced_interrupt_after=args.interrupt_after,
            namespace_count=args.namespaces,
            seed=args.seed,
            initial_shard_bytes=args.initial_shard_bytes,
            shard_growth_factor=args.shard_growth_factor,
            checkpoint_interval=args.checkpoint_interval,
            sqlite_batch_size=args.sqlite_batch_size,
            minimum_free_bytes=args.minimum_free_bytes,
            latency_saturation_seconds_per_10k=args.latency_saturation_seconds,
            rss_saturation_bytes=args.rss_saturation_bytes,
        )
        summary = run_forced_resume_million_frontier(args.output_dir, config=config)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        integrity = summary["manifest"]["integrity"]
        return 0 if (
            summary["exact_total_reached"]
            and integrity["duplicate_ids"] == 0
            and integrity["orphan_parent_count"] == 0
            and integrity["contiguous"]
            and integrity["all_subjects_complete"]
        ) else 1
    if args.command == "plan-additions":
        targets = KnowledgeFrontierTargets(
            cells=args.cells,
            claims_per_cell=args.claims_per_cell,
            evidence_per_claim=args.evidence_per_claim,
            experiments_per_claim=args.experiments_per_claim,
            results_per_experiment=args.results_per_experiment,
            actions_per_result=args.actions_per_result,
            memory_rules_per_result=args.memory_rules_per_result,
            identities_per_claim=args.identities_per_claim,
            benchmark_cases=args.benchmark_cases,
        )
        summary = plan_knowledge_frontier(
            args.output_dir,
            targets=targets,
            initial_shard_bytes=args.initial_shard_bytes,
            shard_growth_factor=args.shard_growth_factor,
            proposed_branch=args.proposed_branch,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["count_matches_target"] and summary["report"]["invalid_records"] == 0 else 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
