from __future__ import annotations

import argparse
import json
from typing import Sequence

from .analysis import analyze_rotor
from .cavitation import assess_cavitation
from .models import OperatingPoint, default_air, default_water, demo_rotor
from .oak import run_propulsion_benchmarks
from .optimizer import OptimizationConstraints, grid_optimize


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-propulsion",
        description="Ω-AERO-HYDRO-PROPULSION-T low-order OAK-safe rotor design kernel.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark", help="Run deterministic OAK gates.")

    analyze = sub.add_parser("analyze-demo", help="Analyze the canonical demonstration rotor.")
    analyze.add_argument("--medium", choices=("air", "water"), default="air")
    analyze.add_argument("--velocity", type=float, default=22.0)
    analyze.add_argument("--rpm", type=float, default=2200.0)
    analyze.add_argument("--collective", type=float, default=0.0)

    optimize = sub.add_parser("optimize-demo", help="Run a compact multiobjective design grid.")
    optimize.add_argument("--medium", choices=("air", "water"), default="air")
    optimize.add_argument("--velocity", type=float, default=22.0)
    optimize.add_argument("--rpm", type=float, default=2200.0)
    optimize.add_argument("--minimum-thrust", type=float, default=1.0)
    optimize.add_argument("--maximum-tip-mach", type=float, default=0.85)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_propulsion_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    medium = default_air() if args.medium == "air" else default_water()
    operating = OperatingPoint(args.velocity, args.rpm, getattr(args, "collective", 0.0))
    rotor = demo_rotor()
    if args.command == "analyze-demo":
        analysis = analyze_rotor(rotor, medium, operating)
        payload = {
            "analysis": analysis.to_dict(),
            "cavitation": assess_cavitation(analysis, medium).to_dict(),
            "epistemic_status": "low-order screening; not flight, marine, structural or regulatory certification",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    report = grid_optimize(
        rotor,
        medium,
        operating,
        diameter_scales=(0.85, 0.925, 1.0, 1.075, 1.15),
        chord_scales=(0.85, 1.0, 1.15),
        pitch_deltas_deg=(-4.0, -2.0, 0.0, 2.0, 4.0),
        constraints=OptimizationConstraints(
            minimum_thrust=args.minimum_thrust,
            maximum_tip_mach=args.maximum_tip_mach,
        ),
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.best is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
