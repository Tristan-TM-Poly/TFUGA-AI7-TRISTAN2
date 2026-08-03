"""CLI for Ω-SPACE-HG-T∞ R0.5 constellations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .r05 import (
    canonical_constellation,
    canonical_targets,
    run_r05_oak_benchmarks,
    simulate_r05_constellation,
)


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-space-hg-r05")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="emit canonical Walker constellation and targets")
    manifest.add_argument("--output")

    simulate = commands.add_parser("simulate", help="run coverage, network, task and migration fixture")
    simulate.add_argument("--duration-hours", type=float, default=24.0)
    simulate.add_argument("--step-s", type=float, default=120.0)
    simulate.add_argument("--fail", action="append", default=[])
    simulate.add_argument("--output")

    oak = commands.add_parser("oak", help="run R0.5 OAKBench")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "manifest":
        payload = {
            "release": "R0.5",
            "constellation": [item.to_dict() for item in canonical_constellation()],
            "targets": [item.__dict__ for item in canonical_targets()],
            "operational_coverage_claimed": False,
            "collision_safety_claimed": False,
            "autonomous_servicing_claimed": False,
        }
    elif arguments.command == "simulate":
        payload = simulate_r05_constellation(
            duration_hours=arguments.duration_hours,
            step_s=arguments.step_s,
            failed_satellites=tuple(arguments.fail),
        )
    elif arguments.command == "oak":
        payload = run_r05_oak_benchmarks()
    else:
        raise AssertionError("unreachable")
    _emit(payload, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
