from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Sequence

from .core import (
    AdaptiveController,
    CapacityPolicy,
    MMinusLedger,
    SyntheticCapacityExecutor,
)
from .github_planner import (
    GitHubDryRunPlanner,
    GitHubPlanPolicy,
    iter_jsonl,
    synthetic_additions,
)
from .governance import (
    IterationObservation,
    ObjectiveVector,
    ReflexMemoryLedger,
    StopGate,
    pareto_front,
)
from .self_improvement import default_scenarios, iter_variants_jsonl
from .self_improvement_judge import ResourceAwareSelfImprovementLab
from .streaming import MPlusLedger, RangeWorkSource, ResourceSampler


def _add_plan_policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--initial-shard-bytes", type=int, default=262_144)
    parser.add_argument("--shard-growth-factor", type=float, default=2.0)
    parser.add_argument("--strict-records", action="store_true")
    parser.add_argument("--require-provenance", action="store_true")
    parser.add_argument("--branch", default="feat/omega-unbounded-generated")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-unbounded",
        description="Ω-SANS-PLAFOND-T∞ adaptive frontier-discovery and GitHub planning engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser(
        "simulate",
        help="Run a finite lazy workload while discovering and surpassing temporary capacity frontiers.",
    )
    simulate.add_argument("--work-items", type=int, default=50_000)
    simulate.add_argument("--initial-batch", type=int, default=256)
    simulate.add_argument("--initial-capacity", type=int, default=1_024)
    simulate.add_argument("--redesign-factor", type=float, default=2.0)
    simulate.add_argument("--quality-floor", type=float, default=0.95)
    simulate.add_argument("--output-dir", default="generated/omega_unbounded_t")
    simulate.add_argument(
        "--no-redesign",
        action="store_true",
        help="Pause at the first discovered frontier instead of adapting the synthetic executor.",
    )

    plan = sub.add_parser(
        "plan",
        help="Compile a JSONL stream of logical additions into a reversible GitHub dry-run tree plan.",
    )
    plan.add_argument("input", help="JSONL file containing one logical addition object per line.")
    plan.add_argument("--output-dir", default="generated/omega_unbounded_github_plan")
    _add_plan_policy_arguments(plan)

    synthetic_plan = sub.add_parser(
        "synthetic-plan",
        help="Stress the streaming GitHub planner with a finite generated workload.",
    )
    synthetic_plan.add_argument("--work-items", type=int, default=100_000)
    synthetic_plan.add_argument("--namespaces", type=int, default=8)
    synthetic_plan.add_argument("--output-dir", default="generated/omega_unbounded_synthetic_plan")
    _add_plan_policy_arguments(synthetic_plan)

    self_improve = sub.add_parser(
        "self-improve",
        help=(
            "Benchmark the current controller against an open candidate stream and emit "
            "an OAK-gated promotion plan without modifying source or GitHub."
        ),
    )
    self_improve.add_argument("--work-items", type=int, default=60_000)
    self_improve.add_argument(
        "--candidates",
        help="Optional JSONL stream of controller variants; consumed until file exhaustion.",
    )
    self_improve.add_argument("--minimum-improvement-ratio", type=float, default=0.02)
    self_improve.add_argument("--overshoot-penalty-weight", type=float, default=10.0)
    self_improve.add_argument("--maximum-overshoot-multiplier", type=float, default=2.0)
    self_improve.add_argument(
        "--output-dir",
        default="generated/omega_unbounded_self_improvement",
    )

    governance = sub.add_parser(
        "governance-check",
        help=(
            "Verify StopGate, reflex M-minus and Pareto invariants without source or remote mutations."
        ),
    )
    governance.add_argument(
        "--output-dir",
        default="generated/omega_unbounded_governance",
    )
    return parser


def _simulate(args: argparse.Namespace) -> int:
    if args.work_items < 0:
        raise ValueError("--work-items cannot be negative")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    sampler = ResourceSampler(output)
    resource_before = sampler.sample()
    source = RangeWorkSource(args.work_items)
    executor = SyntheticCapacityExecutor(
        capacity=args.initial_capacity,
        redesign_factor=args.redesign_factor,
        allow_redesign=not args.no_redesign,
    )
    ledger = MMinusLedger(output / "m_minus.jsonl")
    controller = AdaptiveController(
        source,
        executor,
        initial_batch=args.initial_batch,
        policy=CapacityPolicy(quality_floor=args.quality_floor),
        ledger=ledger,
        checkpoint_path=output / "checkpoint.json",
    )
    report = controller.run()
    resource_after = sampler.sample()

    m_plus = MPlusLedger(output / "m_plus.jsonl")
    for previous, current in zip(executor.frontier_history, executor.frontier_history[1:]):
        m_plus.record(
            previous_frontier=previous,
            new_frontier=current,
            intervention=("synthetic_executor_capacity_redesign",),
            repetitions=1,
            quality_before=executor.quality_score,
            quality_after=executor.quality_score,
            status="experimental_single_run_not_canonized",
        )

    payload = {
        **report.to_dict(),
        "frontier_history": executor.frontier_history,
        "lazy_source": source.checkpoint(),
        "resource_before": resource_before.to_dict(),
        "resource_after": resource_after.to_dict(),
        "m_plus_events": len(m_plus.events),
        "boundary": (
            "No permanent addition-count cap is used. This run is still bounded by its finite workload, "
            "recoverability, quality policy, available resources, and external service rules."
        ),
    }
    (output / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.status == "completed" else 2


def _plan_policy(args: argparse.Namespace) -> GitHubPlanPolicy:
    return GitHubPlanPolicy(
        initial_shard_bytes=args.initial_shard_bytes,
        shard_growth_factor=args.shard_growth_factor,
        strict_records=args.strict_records,
        require_provenance=args.require_provenance,
    )


def _run_plan(args: argparse.Namespace, records: Any) -> int:
    planner = GitHubDryRunPlanner(
        args.output_dir,
        policy=_plan_policy(args),
        proposed_branch=args.branch,
    )
    report = planner.plan(records)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _self_improve(args: argparse.Namespace) -> int:
    scenarios = default_scenarios(args.work_items)
    candidates = iter_variants_jsonl(args.candidates) if args.candidates else None
    report = ResourceAwareSelfImprovementLab(
        args.output_dir,
        scenarios=scenarios,
        minimum_improvement_ratio=args.minimum_improvement_ratio,
        overshoot_penalty_weight=args.overshoot_penalty_weight,
        maximum_overshoot_multiplier=args.maximum_overshoot_multiplier,
    ).run(candidates)
    payload = report.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.baseline.completed else 2


def _governance_check(args: argparse.Namespace) -> int:
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "m_minus_reflex.jsonl"
    if ledger_path.exists():
        ledger_path.unlink()

    ledger = ReflexMemoryLedger(ledger_path)
    rule = ledger.record_overiteration()

    gate = StopGate()
    initial = gate.observe(
        IterationObservation(
            objective_reached=False,
            authoritative_validation=False,
            marginal_information_gain=0.50,
            repetition_score=0.10,
            details=("work still has unresolved evidence",),
        )
    )
    final = gate.observe(
        IterationObservation(
            objective_reached=True,
            authoritative_validation=True,
            marginal_information_gain=0.01,
            repetition_score=0.95,
            validation_fingerprint="governance-ci-proof",
            details=("authoritative evidence obtained",),
        )
    )

    points = (
        ObjectiveVector(
            name="fast",
            maximize={"quality": 1.0, "throughput": 10.0},
            minimize={"memory": 8.0},
        ),
        ObjectiveVector(
            name="lean",
            maximize={"quality": 1.0, "throughput": 8.0},
            minimize={"memory": 4.0},
        ),
        ObjectiveVector(
            name="dominated",
            maximize={"quality": 1.0, "throughput": 7.0},
            minimize={"memory": 9.0},
        ),
    )
    front = pareto_front(points)
    payload = {
        "status": "passed" if final.should_stop else "failed",
        "initial_decision": initial.to_dict(),
        "final_decision": final.to_dict(),
        "negative_memory_rule": rule.to_dict(),
        "known_overiteration_blocked": ledger.is_blocked(
            "repeat_equivalent_validation",
            trigger="objective_reached_and_authoritative_validation_obtained",
        ),
        "pareto_front": [point.to_dict() for point in front],
        "scalar_score_has_final_authority": False,
        "source_mutations": 0,
        "remote_mutations": 0,
    }
    (output / "governance-report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    valid = (
        not initial.should_stop
        and final.should_stop
        and payload["known_overiteration_blocked"] is True
        and {point.name for point in front} == {"fast", "lean"}
        and payload["remote_mutations"] == 0
    )
    return 0 if valid else 2


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "simulate":
            return _simulate(args)
        if args.command == "plan":
            return _run_plan(args, iter_jsonl(args.input))
        if args.command == "synthetic-plan":
            return _run_plan(
                args,
                synthetic_additions(args.work_items, namespaces=args.namespaces),
            )
        if args.command == "self-improve":
            return _self_improve(args)
        if args.command == "governance-check":
            return _governance_check(args)
    except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
        print(f"omega-unbounded: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
