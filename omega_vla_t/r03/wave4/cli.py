"""CLI for Ω-VLA Wave 4 Counterexample Superfactory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .engine import BUILTINS, CounterexampleFrontier, execute_builtin_campaign, plan_campaign, run_oakbench


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-wave4")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output")

    decode = commands.add_parser("decode")
    decode.add_argument("index", type=int)
    decode.add_argument("--output")

    plan = commands.add_parser("plan")
    plan.add_argument("--start-offset", type=int, default=0)
    plan.add_argument("--count", type=int, default=128)
    plan.add_argument("--output")

    search = commands.add_parser("search")
    search.add_argument("conjecture", choices=sorted(BUILTINS))
    search.add_argument("--dimension", type=int, default=2)
    search.add_argument("--scalar-system", choices=("real", "complex"), default="real")
    search.add_argument("--family", default="dense")
    search.add_argument("--seed", type=int, default=2026)
    search.add_argument("--trials", type=int, default=16)
    search.add_argument("--no-minimize", action="store_true")
    search.add_argument("--output")

    oak = commands.add_parser("oak")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "manifest":
        payload = {
            "wave": "R0.3-Wave4-Counterexample-Superfactory",
            "frontier": CounterexampleFrontier().manifest(),
            "builtins": sorted(BUILTINS),
        }
    elif arguments.command == "decode":
        frontier = CounterexampleFrontier()
        address = frontier.decode(arguments.index)
        payload = {
            "logical_index": arguments.index,
            "address": address.to_dict(),
            "roundtrip_index": frontier.encode(address),
        }
    elif arguments.command == "plan":
        payload = plan_campaign(arguments.start_offset, arguments.count)
    elif arguments.command == "search":
        payload = execute_builtin_campaign(
            arguments.conjecture,
            dimension=arguments.dimension,
            scalar_system=arguments.scalar_system,
            family=arguments.family,
            seed=arguments.seed,
            trials=arguments.trials,
            minimize=not arguments.no_minimize,
        )
    elif arguments.command == "oak":
        payload = run_oakbench()
    else:
        raise AssertionError("unreachable")
    _emit(payload, getattr(arguments, "output", None))
    return 0 if not isinstance(payload, dict) or payload.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
