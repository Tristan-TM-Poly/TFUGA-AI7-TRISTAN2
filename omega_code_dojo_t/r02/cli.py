from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .benchmark import fixture_provenance, run_r02_benchmark
from .campaign import CampaignEngine
from .frontier import DEFAULT_FRONTIER
from .models import CampaignPolicy


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-code-dojo-r02",
        description="Ω-CODE-DOJO-T∞ R0.2 logical frontier and OAK campaign engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    frontier = subparsers.add_parser("frontier", help="Inspect the logical address space.")
    frontier.add_argument("--sample", type=int, default=4)
    frontier.add_argument("--output")

    campaign = subparsers.add_parser("campaign", help="Run a finite adaptive campaign.")
    campaign.add_argument("--budget", type=int, default=32)
    campaign.add_argument("--permanent-cap", type=int)
    campaign.add_argument("--output")

    benchmark = subparsers.add_parser("benchmark", help="Run deterministic R0.2 OAKBench.")
    benchmark.add_argument("--budget", type=int, default=32)
    benchmark.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "frontier":
        sample_count = max(0, min(args.sample, 64))
        sample = [DEFAULT_FRONTIER.cell_at(index).to_dict() for index in range(sample_count)]
        _write({**DEFAULT_FRONTIER.to_dict(), "sample": sample}, args.output)
        return 0

    if args.command == "campaign":
        policy = CampaignPolicy(
            materialization_budget=args.budget,
            permanent_cap=args.permanent_cap,
        )
        receipt = CampaignEngine().run(policy, fixture_provenance())
        _write(receipt.to_dict(), args.output)
        return 0 if receipt.materialized_cells > 0 else 1

    payload = run_r02_benchmark(args.budget)
    _write(payload, args.output)
    return (
        0
        if payload["status"] == "CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
