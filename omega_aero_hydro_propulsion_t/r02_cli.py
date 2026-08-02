from __future__ import annotations

import argparse
import json
from typing import Sequence

from .annular_bem import analyze_annular_bem
from .mission import demo_air_mission, evaluate_mission
from .models import BladeStation, OperatingPoint, RotorDesign, default_air, demo_rotor
from .polars import PolarRegistry, demo_polar_table
from .r02_oak import run_r02_benchmarks


def _tabulated_demo_rotor() -> tuple[RotorDesign, PolarRegistry]:
    base = demo_rotor()
    design = RotorDesign(
        name="tabulated-polar-demo-rotor",
        blade_count=base.blade_count,
        hub_radius=base.hub_radius,
        tip_radius=base.tip_radius,
        stations=tuple(
            BladeStation(station.radius, station.chord, station.twist_deg, "demo-tabulated-symmetric")
            for station in base.stations
        ),
    )
    return design, PolarRegistry([demo_polar_table()])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-propulsion-r02",
        description="Ω-AERO-HYDRO-PROPULSION-T R0.2 annular BEM, polar registry and mission kernel.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark", help="Run R0.2 OAK gates.")

    annular = sub.add_parser("annular-demo", help="Run annular BEM on the canonical rotor.")
    annular.add_argument("--velocity", type=float, default=22.0)
    annular.add_argument("--rpm", type=float, default=2_200.0)
    annular.add_argument("--collective", type=float, default=0.0)
    annular.add_argument("--tabulated-polar", action="store_true")

    sub.add_parser("polar-demo", help="Inspect and interpolate the deterministic tabulated polar fixture.")
    sub.add_parser("mission-demo", help="Evaluate the canonical three-phase aerial mission.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r02_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2
    if args.command == "polar-demo":
        table = demo_polar_table()
        payload = {
            "table": table.to_dict(),
            "interpolation": table.evaluate(7.5, reynolds=300_000.0, mach=0.12).to_dict(),
            "epistemic_status": "synthetic regression fixture; not measured aerodynamic evidence",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.command == "mission-demo":
        report = evaluate_mission(demo_rotor(), default_air(), demo_air_mission())
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.feasible else 2

    registry = None
    design = demo_rotor()
    if args.tabulated_polar:
        design, registry = _tabulated_demo_rotor()
    analysis = analyze_annular_bem(
        design,
        default_air(),
        OperatingPoint(args.velocity, args.rpm, args.collective),
        registry=registry,
    )
    print(json.dumps(analysis.to_dict(), indent=2, sort_keys=True))
    return 0 if analysis.converged else 2


if __name__ == "__main__":
    raise SystemExit(main())
