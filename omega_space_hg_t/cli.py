"""Command-line interface for Ω-SPACE-HG-T∞ R0.1."""
from __future__ import annotations

import argparse
from typing import Any

from .atlas import atlas_manifest
from .io import emit_json, load_mission
from .mission import compile_mission_hypergraph, simulate_mission
from .oak import canonical_6u_mission, run_oak_benchmarks
from .optimization import UnboundedDesignFrontier, optimize_designs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-space-hg")
    commands = parser.add_subparsers(dest="command", required=True)

    atlas = commands.add_parser("atlas", help="emit the generative space-system taxonomy")
    atlas.add_argument("--output")

    manifest = commands.add_parser("manifest", help="emit the canonical 6U mission manifest")
    manifest.add_argument("--output")

    graph = commands.add_parser("graph", help="compile an evidence-bearing mission hypergraph")
    graph.add_argument("mission", nargs="?", help="mission JSON; canonical fixture when omitted")
    graph.add_argument("--output")

    simulate = commands.add_parser("simulate", help="run orbit-power-thermal-data co-simulation")
    simulate.add_argument("mission", nargs="?", help="mission JSON; canonical fixture when omitted")
    simulate.add_argument("--summary-only", action="store_true")
    simulate.add_argument("--output")

    plan = commands.add_parser("plan", help="address a resumable unbounded design frontier")
    plan.add_argument("--start-offset", type=int, default=0)
    plan.add_argument("--count", type=int, default=128)
    plan.add_argument("--output")

    optimize = commands.add_parser("optimize", help="evaluate designs and emit a Pareto front")
    optimize.add_argument("mission", nargs="?", help="mission JSON; canonical fixture when omitted")
    optimize.add_argument("--start-offset", type=int, default=0)
    optimize.add_argument("--count", type=int, default=32)
    optimize.add_argument("--output")

    oak = commands.add_parser("oak", help="run deterministic OAKBench gates")
    oak.add_argument("--output")
    return parser


def _mission(path: str | None):
    return load_mission(path) if path else canonical_6u_mission()


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    payload: Any
    if arguments.command == "atlas":
        payload = atlas_manifest()
    elif arguments.command == "manifest":
        payload = canonical_6u_mission().to_dict()
    elif arguments.command == "graph":
        payload = compile_mission_hypergraph(_mission(arguments.mission))
    elif arguments.command == "simulate":
        payload = simulate_mission(_mission(arguments.mission)).to_dict(
            include_points=not arguments.summary_only
        )
    elif arguments.command == "plan":
        payload = UnboundedDesignFrontier().plan(arguments.start_offset, arguments.count)
    elif arguments.command == "optimize":
        payload = optimize_designs(
            _mission(arguments.mission),
            start_offset=arguments.start_offset,
            count=arguments.count,
        )
    elif arguments.command == "oak":
        payload = run_oak_benchmarks()
    else:
        raise AssertionError("unreachable")
    text = emit_json(payload, arguments.output)
    if arguments.output is None:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
