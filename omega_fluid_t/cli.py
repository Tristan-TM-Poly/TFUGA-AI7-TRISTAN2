from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .dimensionless import DimensionlessInput, compute_dimensionless
from .frontier import FrontierWriter, WriterPolicy, default_fluid_space
from .oak import run_core_benchmarks


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-fluid",
        description="Ω-FLUID-T∞² OAK-safe fluid research kernel and unbounded epoch frontier.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dim = sub.add_parser("dimensionless", help="Compute a guarded set of dimensionless numbers.")
    dim.add_argument("--density", type=float, required=True)
    dim.add_argument("--velocity", type=float, required=True)
    dim.add_argument("--length", type=float, required=True)
    dim.add_argument("--dynamic-viscosity", type=float, required=True)
    dim.add_argument("--sound-speed", type=float)
    dim.add_argument("--gravity", type=float)
    dim.add_argument("--surface-tension", type=float)
    dim.add_argument("--thermal-diffusivity", type=float)
    dim.add_argument("--mass-diffusivity", type=float)
    dim.add_argument("--kinematic-viscosity", type=float)
    dim.add_argument("--frequency", type=float)
    dim.add_argument("--mean-free-path", type=float)
    dim.add_argument("--relaxation-time", type=float)

    sub.add_parser("benchmark", help="Run compact analytic and numerical OAK baselines.")

    plan = sub.add_parser("frontier-plan", help="Plan a finite window in the epoch-indexed address space.")
    plan.add_argument("--start", type=int, default=0)
    plan.add_argument("--count", type=int, required=True)
    plan.add_argument("--estimated-bytes-per-record", type=int, default=900)

    materialize = sub.add_parser("frontier-materialize", help="Materialize a finite, resumable JSONL frontier window.")
    materialize.add_argument("--start", type=int, default=0)
    materialize.add_argument("--count", type=int, required=True)
    materialize.add_argument("--output-dir", default="generated/omega_fluid_frontier")
    materialize.add_argument("--target-shard-bytes", type=int, default=8 * 1024 * 1024)
    materialize.add_argument("--checkpoint-interval", type=int, default=10_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "dimensionless":
            fields = vars(args).copy()
            fields.pop("command")
            result = compute_dimensionless(DimensionlessInput(**fields))
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return 0
        if args.command == "benchmark":
            report = run_core_benchmarks()
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            return 0 if report.passed else 2
        if args.command == "frontier-plan":
            plan = default_fluid_space().plan(
                start=args.start,
                count=args.count,
                estimated_bytes_per_record=args.estimated_bytes_per_record,
            )
            print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
            return 0
        if args.command == "frontier-materialize":
            writer = FrontierWriter(
                Path(args.output_dir),
                policy=WriterPolicy(
                    target_shard_bytes=args.target_shard_bytes,
                    checkpoint_interval=args.checkpoint_interval,
                ),
            )
            manifest = writer.materialize(default_fluid_space(), start=args.start, count=args.count)
            print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"omega-fluid: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
