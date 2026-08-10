from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .actions_bridge import collect_trigger_hotspots
from .engine import build_report
from .evidence_subgraph import compile_evidence_subgraph
from .frontier_bridge import BackpressureState, decide_backpressure
from .github_telemetry import build_actions_snapshot
from .policy_lab import PolicyOutcome, compare_policies
from .search_lab import run_multifidelity_beam
from .work_ir import compile_work_ir


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("input must be a JSON object")
    return payload


def _write_or_print(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-workmax")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="compile a WorkPacket campaign into an OAK review report")
    plan.add_argument("input")
    plan.add_argument("--output")

    hotspots = sub.add_parser("actions-hotspots", help="reuse Ω-ACTIONS trigger-hotspot analysis")
    hotspots.add_argument("--root", default=".")
    hotspots.add_argument("--output")

    telemetry = sub.add_parser("telemetry", help="compile immutable exported GitHub run/job payloads")
    telemetry.add_argument("input", help="JSON object with runs, jobs_by_run and observed_at")
    telemetry.add_argument("--output")

    workir = sub.add_parser("workir", help="compile intent + deltas + issues + capabilities + OAK residues")
    workir.add_argument("input")
    workir.add_argument("--output")

    evidence = sub.add_parser("evidence-subgraph", help="compile conservative ΔCI proof subgraph")
    evidence.add_argument("input", help="JSON object containing delta_report and optional required_workflows")
    evidence.add_argument("--output")

    backpressure = sub.add_parser("backpressure", help="compute validation-absorption backpressure")
    backpressure.add_argument("input")
    backpressure.add_argument("--output")

    beam = sub.add_parser("beam-search", help="run deterministic multi-fidelity beam policy search")
    beam.add_argument("input")
    beam.add_argument("--output")

    policy = sub.add_parser("policy-lab", help="compare finite scheduler-policy outcomes")
    policy.add_argument("input")
    policy.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "plan":
        _write_or_print(build_report(_load(args.input)), args.output)
        return 0
    if args.command == "actions-hotspots":
        _write_or_print(collect_trigger_hotspots(args.root), args.output)
        return 0
    if args.command == "telemetry":
        payload = _load(args.input)
        _write_or_print(
            build_actions_snapshot(
                payload.get("runs", []),
                payload.get("jobs_by_run", {}),
                observed_at=str(payload["observed_at"]),
            ),
            args.output,
        )
        return 0
    if args.command == "workir":
        _write_or_print(compile_work_ir(_load(args.input)), args.output)
        return 0
    if args.command == "evidence-subgraph":
        payload = _load(args.input)
        _write_or_print(
            compile_evidence_subgraph(
                payload.get("delta_report", {}),
                required_workflows=payload.get("required_workflows", []),
            ),
            args.output,
        )
        return 0
    if args.command == "backpressure":
        payload = _load(args.input)
        _write_or_print(decide_backpressure(BackpressureState(**payload)), args.output)
        return 0
    if args.command == "beam-search":
        _write_or_print(run_multifidelity_beam(_load(args.input)), args.output)
        return 0
    if args.command == "policy-lab":
        payload = _load(args.input)
        outcomes = [PolicyOutcome(**row) for row in payload.get("outcomes", [])]
        _write_or_print(
            compare_policies(
                outcomes,
                incumbent_policy_id=str(payload["incumbent_policy_id"]),
                minimum_wall_improvement=float(payload.get("minimum_wall_improvement", 0.02)),
            ),
            args.output,
        )
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
