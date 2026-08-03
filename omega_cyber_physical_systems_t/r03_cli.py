from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from .hybrid import demo_zeno_automaton, simulate_hybrid_automaton
from .r03_fixtures import (
    r03_adversarial_initial_box,
    r03_axis_automaton,
    r03_initial_box,
    r03_temporal_properties,
    r03_unsafe_condition,
)
from .r03_oak import run_cps_r03_benchmarks
from .reachability import bounded_reachability
from .temporal import verify_temporal_properties


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-cps-r03",
        description="Ω-CPS R0.3 hybrid automata, temporal contracts, Zeno guards and bounded reachability",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")
    sub.add_parser("automaton-demo")

    hybrid = sub.add_parser("hybrid-demo")
    hybrid.add_argument("--summary-only", action="store_true")
    hybrid.add_argument("--horizon-s", type=float, default=1.30)
    hybrid.add_argument("--dt-s", type=float, default=0.001)

    temporal = sub.add_parser("temporal-demo")
    temporal.add_argument("--summary-only", action="store_true")

    reachability = sub.add_parser("reachability-demo")
    reachability.add_argument("--adversarial", action="store_true")
    reachability.add_argument("--summary-only", action="store_true")
    reachability.add_argument("--steps", type=int, default=24)
    reachability.add_argument("--dt-s", type=float, default=0.05)
    reachability.add_argument("--node-budget", type=int, default=4096)

    zeno = sub.add_parser("zeno-demo")
    zeno.add_argument("--summary-only", action="store_true")
    return parser


def _hybrid_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "automaton_id": payload["automaton_id"],
        "sample_count": payload["sample_count"],
        "event_count": payload["event_count"],
        "event_sequence": [item["transition_id"] for item in payload["events"]],
        "final_mode": payload["final_mode"],
        "final_state": payload["final_state"],
        "invariant_violation_count": payload["invariant_violation_count"],
        "unsafe_sample_count": payload["unsafe_sample_count"],
        "zeno_suspected": payload["zeno_suspected"],
        "transition_limit_hit": payload["transition_limit_hit"],
        "finite": payload["finite"],
        "evidence_hash": payload["evidence_hash"],
        "physics_certified": payload["physics_certified"],
        "safety_certified": payload["safety_certified"],
        "formal_reachability_proven": payload["formal_reachability_proven"],
    }


def _temporal_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": payload["passed"],
        "property_count": payload["property_count"],
        "passed_count": payload["passed_count"],
        "violation_count": payload["violation_count"],
        "properties": [
            {
                "property_id": item["property"]["property_id"],
                "kind": item["property"]["kind"],
                "passed": item["passed"],
                "trigger_count": item["trigger_count"],
                "violation_count": item["violation_count"],
            }
            for item in payload["results"]
        ],
        "evidence_hash": payload["evidence_hash"],
        "formal_proof": payload["formal_proof"],
        "safety_certified": payload["safety_certified"],
    }


def _reachability_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "steps_requested": payload["steps_requested"],
        "steps_completed": payload["steps_completed"],
        "node_count": payload["node_count"],
        "transition_branch_count": payload["transition_branch_count"],
        "invariant_pruned_count": payload["invariant_pruned_count"],
        "uncertain_invariant_count": payload["uncertain_invariant_count"],
        "unsafe_possible_count": payload["unsafe_possible_count"],
        "unsafe_definite_count": payload["unsafe_definite_count"],
        "truncated": payload["truncated"],
        "execution_node_budget": payload["execution_node_budget"],
        "permanent_total_cap": payload["permanent_total_cap"],
        "evidence_hash": payload["evidence_hash"],
        "formal_reachability_proven": payload["formal_reachability_proven"],
        "safety_certified": payload["safety_certified"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_cps_r03_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    automaton = r03_axis_automaton()
    if args.command == "automaton-demo":
        print(json.dumps(automaton.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "hybrid-demo":
        report = simulate_hybrid_automaton(
            automaton,
            horizon_s=args.horizon_s,
            integration_step_s=args.dt_s,
        )
        payload = report.to_dict()
        print(json.dumps(_hybrid_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0 if report.finite and report.invariant_violation_count == 0 else 2

    if args.command == "temporal-demo":
        trace = simulate_hybrid_automaton(automaton, horizon_s=1.30, integration_step_s=0.001)
        report = verify_temporal_properties(trace, r03_temporal_properties())
        payload = report.to_dict()
        print(json.dumps(_temporal_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0 if report.passed else 2

    if args.command == "reachability-demo":
        initial_box = r03_adversarial_initial_box() if args.adversarial else r03_initial_box()
        report = bounded_reachability(
            automaton,
            initial_box=initial_box,
            integration_step_s=args.dt_s,
            steps=args.steps,
            unsafe_conditions=r03_unsafe_condition(),
            max_nodes_per_step=args.node_budget,
            numerical_widening_per_step=0.0 if args.adversarial else 1e-8,
        )
        payload = report.to_dict()
        print(json.dumps(_reachability_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0 if report.unsafe_possible_count == 0 and not report.truncated else 2

    report = simulate_hybrid_automaton(
        demo_zeno_automaton(),
        horizon_s=0.1,
        integration_step_s=0.01,
        max_transitions_per_step=8,
        zeno_window_s=0.02,
        zeno_transition_threshold=6,
    )
    payload = report.to_dict()
    print(json.dumps(_hybrid_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
    detected = report.zeno_suspected or report.transition_limit_hit
    return 0 if detected else 2


if __name__ == "__main__":
    raise SystemExit(main())
