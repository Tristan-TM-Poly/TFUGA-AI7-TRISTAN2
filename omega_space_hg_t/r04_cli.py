"""CLI for Ω-SPACE-HG-T∞ R0.4 reliability and FDIR."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .r04 import (
    canonical_common_causes,
    canonical_components,
    canonical_fault_tree,
    canonical_radiation,
    run_r04_oak_benchmarks,
    simulate_fdir_scenario,
    simulate_r04_campaign,
)


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-space-hg-r04")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="emit canonical reliability fixture")
    manifest.add_argument("--duration-days", type=float, default=365.25)
    manifest.add_argument("--output")

    campaign = commands.add_parser("campaign", help="run a resumable deterministic reliability campaign")
    campaign.add_argument("--duration-days", type=float, default=365.25)
    campaign.add_argument("--start-offset", type=int, default=0)
    campaign.add_argument("--count", type=int, default=2048)
    campaign.add_argument("--no-common-causes", action="store_true")
    campaign.add_argument("--no-radiation", action="store_true")
    campaign.add_argument("--output")

    fdir = commands.add_parser("fdir", help="run the canonical permission-bounded FDIR path")
    fdir.add_argument("--output")

    oak = commands.add_parser("oak", help="run R0.4 OAKBench")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "manifest":
        payload = {
            "release": "R0.4",
            "duration_days": arguments.duration_days,
            "components": [item.__dict__ for item in canonical_components()],
            "common_causes": [item.__dict__ for item in canonical_common_causes()],
            "radiation": canonical_radiation().__dict__,
            "independent_fault_tree_probability": canonical_fault_tree(arguments.duration_days).probability(),
            "operational_reliability_claimed": False,
            "safety_certification_claimed": False,
        }
    elif arguments.command == "campaign":
        payload = simulate_r04_campaign(
            duration_days=arguments.duration_days,
            start_offset=arguments.start_offset,
            count=arguments.count,
            include_common_causes=not arguments.no_common_causes,
            include_radiation=not arguments.no_radiation,
        )
    elif arguments.command == "fdir":
        payload = simulate_fdir_scenario()
    elif arguments.command == "oak":
        payload = run_r04_oak_benchmarks()
    else:
        raise AssertionError("unreachable")
    _emit(payload, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
