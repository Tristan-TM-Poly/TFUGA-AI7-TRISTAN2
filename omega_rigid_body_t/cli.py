from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .euler_top import (
    Invariants,
    PrincipalInertia,
    classify_regime,
    elliptic_parameters,
    invariants_from_state,
    sample_analytic,
    separatrix_omega,
)
from .oak import run_oak_benchmarks


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-rigid-body",
        description="Ω-RIGID-BODY-T exact triaxial Euler-top and OAK cross-check kernel.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze-state", help="Compute invariants and classify an initial angular velocity.")
    _add_inertia(analyze)
    analyze.add_argument("--omega", nargs=3, type=float, required=True, metavar=("W1", "W2", "W3"))

    sample = sub.add_parser("sample", help="Sample a canonical exact elliptic branch.")
    _add_inertia(sample)
    sample.add_argument("--energy", type=float, required=True)
    sample.add_argument("--angular-momentum", type=float, required=True)
    sample.add_argument("--phase", type=float, default=0.0)
    sample.add_argument("--duration", type=float, required=True)
    sample.add_argument("--count", type=int, default=129)

    separatrix = sub.add_parser("separatrix", help="Sample the exact hyperbolic intermediate-axis separatrix.")
    _add_inertia(separatrix)
    separatrix.add_argument("--angular-momentum", type=float, required=True)
    separatrix.add_argument("--duration", type=float, required=True)
    separatrix.add_argument("--count", type=int, default=129)

    sub.add_parser("benchmark", help="Run dependency-free analytic/computational OAKBench.")
    return parser


def _add_inertia(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--inertia", nargs=3, type=float, required=True, metavar=("I1", "I2", "I3"))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "benchmark":
            report = run_oak_benchmarks()
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            return 0 if report.passed else 2

        inertia = PrincipalInertia(*args.inertia)
        if args.command == "analyze-state":
            invariants = invariants_from_state(inertia, args.omega)
            payload = {
                "inertia": inertia.to_dict(),
                "omega": args.omega,
                "invariants": invariants.to_dict(),
                "regime": classify_regime(inertia, invariants),
                "claim_status": "exact torque-free invariant classification",
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        if args.count < 2:
            raise ValueError("count must be at least two")
        if args.duration <= 0.0:
            raise ValueError("duration must be positive")
        times = [args.duration * index / (args.count - 1) for index in range(args.count)]

        if args.command == "sample":
            invariants = Invariants(
                energy=args.energy,
                angular_momentum_squared=args.angular_momentum**2,
            )
            parameters = elliptic_parameters(inertia, invariants)
            payload = {
                "inertia": inertia.to_dict(),
                "invariants": invariants.to_dict(),
                "parameters": parameters.to_dict(),
                "samples": [sample.to_dict() for sample in sample_analytic(inertia, invariants, times, phase=args.phase)],
                "physical_experiment_certified": False,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        if args.command == "separatrix":
            payload = {
                "inertia": inertia.to_dict(),
                "angular_momentum": args.angular_momentum,
                "samples": [
                    {"time": time, "omega": list(separatrix_omega(time, inertia, args.angular_momentum))}
                    for time in times
                ],
                "physical_experiment_certified": False,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
    except (ArithmeticError, TypeError, ValueError) as exc:
        print(f"omega-rigid-body: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
