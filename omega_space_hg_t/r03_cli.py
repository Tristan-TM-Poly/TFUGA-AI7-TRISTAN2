"""CLI for Ω-SPACE-HG-T∞ R0.3 networks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .r03 import (
    canonical_battery,
    canonical_ground_station,
    canonical_thermal_network,
    run_r03_oak_benchmarks,
    simulate_r03_networks,
)


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-space-hg-r03")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="emit canonical network fixture metadata")
    manifest.add_argument("--output")

    simulate = commands.add_parser("simulate", help="run coupled thermal EPS RF ground and data simulation")
    simulate.add_argument("--duration-orbits", type=float, default=8.0)
    simulate.add_argument("--step-s", type=float, default=20.0)
    simulate.add_argument("--output")

    oak = commands.add_parser("oak", help="run R0.3 OAKBench")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "manifest":
        thermal = canonical_thermal_network()
        payload = {
            "release": "R0.3",
            "ground_station": canonical_ground_station().__dict__,
            "battery": canonical_battery().__dict__,
            "thermal_nodes": [node.__dict__ for node in thermal.nodes.values()],
            "thermal_conductances": [edge.__dict__ for edge in thermal.conductances],
            "operational_network_claimed": False,
            "flight_qualified_claimed": False,
            "regulatory_approval_claimed": False,
        }
    elif arguments.command == "simulate":
        payload = simulate_r03_networks(
            duration_orbits=arguments.duration_orbits,
            step_s=arguments.step_s,
        )
    elif arguments.command == "oak":
        payload = run_r03_oak_benchmarks()
    else:
        raise AssertionError("unreachable")
    _emit(payload, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
