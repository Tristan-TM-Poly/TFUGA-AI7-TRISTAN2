"""Command line interface for Ω-MILLENNIUM-T∞ R0.1."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .benchmark import poincare_dependency_fixture, run_benchmark
from .campaign import compile_campaign
from .formal_bridge import export_lean_skeleton
from .models import Claim, ClaimKind, OAKLevel, ProblemId
from .registry import all_problems, validate_registry


def registry_payload() -> dict[str, Any]:
    return {
        "schema": "omega-millennium-registry/1",
        "problems": [asdict(problem) for problem in all_problems()],
        "errors": validate_registry(),
        "solution_claimed": False,
    }


def graph_payload() -> dict[str, Any]:
    graph = poincare_dependency_fixture()
    seeds = ("closed-simply-connected-3m", "ricci-flow-framework")
    reached = graph.reachable_claims(seeds, minimum_level=OAKLevel.RESTRICTED_PROOF)
    return {
        "schema": "omega-millennium-graph-demo/1",
        "problem_id": graph.problem_id.value,
        "digest": graph.digest(),
        "reached": sorted(reached),
        "report": asdict(graph.validate()),
        "benchmark_only": True,
    }


def formal_payload() -> dict[str, Any]:
    claim = Claim(
        claim_id="ns_fixture_energy_lemma",
        problem_id=ProblemId.NAVIER_STOKES,
        kind=ClaimKind.LEMMA,
        statement="A declared restricted fixture satisfies an energy estimate.",
        assumptions=("smooth_fixture", "divergence_free_fixture"),
        oak_level=OAKLevel.WELL_TYPED,
        scope="restricted fixture only",
    )
    return asdict(export_lean_skeleton(claim))


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-millennium")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("registry", "graph-demo", "benchmark", "formal-demo"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--output")

    campaign = subparsers.add_parser("campaign")
    campaign.add_argument("--budget", type=int, default=100)
    campaign.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "registry":
        payload = registry_payload()
    elif args.command == "graph-demo":
        payload = graph_payload()
    elif args.command == "benchmark":
        payload = run_benchmark()
    elif args.command == "formal-demo":
        payload = formal_payload()
    elif args.command == "campaign":
        payload = compile_campaign(total_budget_units=args.budget)
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2
    _write(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
