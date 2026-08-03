from __future__ import annotations

import argparse
import json
from typing import Sequence

from .cosim import demo_fault_scenario, demo_nominal_scenario, run_closed_loop_axis
from .energy_graph import audit_closed_loop_energy
from .models import demo_electromechanical_axis_blueprint
from .r02_oak import run_cps_r02_benchmarks
from .unit_graph import audit_blueprint_units, default_unit_registry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-cps-r02",
        description="Omega CPS R0.2 dimensional and energy audit CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")
    sub.add_parser("unit-demo")
    energy = sub.add_parser("energy-demo")
    energy.add_argument("--faulted", action="store_true")
    energy.add_argument("--untracked-output-j", type=float, default=0.0)
    energy.add_argument("--summary-only", action="store_true")
    convert = sub.add_parser("convert")
    convert.add_argument("value", type=float)
    convert.add_argument("source")
    convert.add_argument("target")
    return parser


def _energy_summary(payload: dict) -> dict:
    return {
        "scenario_id": payload["scenario_id"],
        "sample_count": payload["sample_count"],
        "global_supplied_energy_j": payload["global_supplied_energy_j"],
        "global_accounted_energy_j": payload["global_accounted_energy_j"],
        "global_residual_j": payload["global_residual_j"],
        "global_normalized_residual": payload["global_normalized_residual"],
        "residual_tolerance_j": payload["residual_tolerance_j"],
        "balance_passed": payload["balance_passed"],
        "passivity": payload["passivity"],
        "evidence_hash": payload["evidence_hash"],
        "energy_conservation_proven": payload["energy_conservation_proven"],
        "physics_certified": payload["physics_certified"],
        "hardware_validated": payload["hardware_validated"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_cps_r02_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2
    if args.command == "unit-demo":
        report = audit_blueprint_units(demo_electromechanical_axis_blueprint())
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.dimensionally_valid else 2
    if args.command == "convert":
        registry = default_unit_registry()
        converted = registry.convert(args.value, args.source, args.target)
        print(json.dumps({
            "value": args.value,
            "source": args.source,
            "target": args.target,
            "converted": converted,
            "dimension": registry.get(args.source).to_dict()["dimension"],
        }, indent=2, sort_keys=True))
        return 0
    scenario = demo_fault_scenario() if args.faulted else demo_nominal_scenario()
    simulation = run_closed_loop_axis(scenario)
    report = audit_closed_loop_energy(simulation, untracked_output_energy_j=args.untracked_output_j)
    payload = report.to_dict()
    print(json.dumps(_energy_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
    return 0 if report.balance_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
