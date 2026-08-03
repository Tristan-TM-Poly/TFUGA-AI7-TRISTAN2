"""Command-line interface for Ω-RIGID-BODY-T R0.2."""
from __future__ import annotations

import argparse
import json
from math import cos, sin
from pathlib import Path
import sys
from typing import Sequence

from .analytic import exact_parameters_from_state
from .atlas import atlas_manifest, default_atlas_config, stroboscopic_map
from .geometry import phase_closure_report
from .integrators import integrate_midpoint_torque_free, simulate_adaptive
from .model import PrincipalMoments, principal_axis_stability
from .oak import run_oak_benchmarks


def _triplet(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) != 3:
        raise ValueError("expected exactly three values")
    return (float(values[0]), float(values[1]), float(values[2]))


def _model(args) -> PrincipalMoments:
    return PrincipalMoments(args.i1, args.i2, args.i3)


def _base_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--i1", type=float, required=True)
    parser.add_argument("--i2", type=float, required=True)
    parser.add_argument("--i3", type=float, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-rigid-body-r02",
        description="Ω-RIGID-BODY-T R0.2 exact phase, geometric phase, forcing and OAKBench.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fit = sub.add_parser("fit", help="Recover the exact elliptic branch from arbitrary initial omega.")
    _base_parser(fit)
    fit.add_argument("--omega", type=float, nargs=3, required=True)
    fit.add_argument("--phase-grid", type=int, default=2048)

    phase = sub.add_parser("phase", help="Compare Montgomery phase with quaternion monodromy.")
    _base_parser(phase)
    phase.add_argument("--omega", type=float, nargs=3, required=True)
    phase.add_argument("--samples", type=int, default=2048)

    simulate = sub.add_parser("simulate", help="Adaptive forced/damped body-plus-orientation simulation.")
    _base_parser(simulate)
    simulate.add_argument("--omega", type=float, nargs=3, required=True)
    simulate.add_argument("--t-end", type=float, required=True)
    simulate.add_argument("--samples", type=int, default=256)
    simulate.add_argument("--constant-torque", type=float, nargs=3, default=(0.0, 0.0, 0.0))
    simulate.add_argument("--damping", type=float, default=0.0)
    simulate.add_argument("--rtol", type=float, default=1e-10)
    simulate.add_argument("--atol", type=float, default=1e-12)
    simulate.add_argument("--summary-only", action="store_true")

    midpoint = sub.add_parser("midpoint", help="Invariant-preserving torque-free implicit midpoint run.")
    _base_parser(midpoint)
    midpoint.add_argument("--omega", type=float, nargs=3, required=True)
    midpoint.add_argument("--t-end", type=float, required=True)
    midpoint.add_argument("--steps", type=int, required=True)

    stability = sub.add_parser("stability", help="Linearized principal-axis stability spectrum.")
    _base_parser(stability)
    stability.add_argument("--angular-speed", type=float, required=True)

    poincare = sub.add_parser("poincare", help="Stroboscopic map for sinusoidal body torque.")
    _base_parser(poincare)
    poincare.add_argument("--omega", type=float, nargs=3, required=True)
    poincare.add_argument("--forcing-period", type=float, required=True)
    poincare.add_argument("--cycles", type=int, required=True)
    poincare.add_argument("--torque-amplitude", type=float, nargs=3, required=True)
    poincare.add_argument("--damping", type=float, default=0.0)

    atlas = sub.add_parser("atlas", help="Generate a deterministic inertia-energy research atlas.")
    atlas.add_argument("--inertia-count", type=int, default=8)
    atlas.add_argument("--energy-count", type=int, default=32)
    atlas.add_argument("--angular-momentum", type=float, default=1.0)
    atlas.add_argument("--output")

    benchmark = sub.add_parser("benchmark", help="Run deterministic R0.2 OAKBench.")
    benchmark.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "fit":
            result = exact_parameters_from_state(_model(args), _triplet(args.omega), phase_grid=args.phase_grid)
            payload = result.to_dict()
        elif args.command == "phase":
            model = _model(args)
            parameters = exact_parameters_from_state(model, _triplet(args.omega))
            payload = {
                "exact_parameters": parameters.to_dict(),
                "phase_closure": phase_closure_report(model, parameters, samples=args.samples).to_dict(),
            }
        elif args.command == "simulate":
            torque_vector = _triplet(args.constant_torque)
            torque = lambda time, omega, q: torque_vector
            result = simulate_adaptive(
                _model(args),
                _triplet(args.omega),
                t_end=args.t_end,
                samples=args.samples,
                torque=torque,
                damping=args.damping,
                rtol=args.rtol,
                atol=args.atol,
            )
            payload = result.to_dict(include_samples=not args.summary_only)
        elif args.command == "midpoint":
            payload = integrate_midpoint_torque_free(
                _model(args), _triplet(args.omega), t_end=args.t_end, steps=args.steps
            ).to_dict()
        elif args.command == "stability":
            model = _model(args)
            payload = {
                "modes": [
                    principal_axis_stability(model, axis, args.angular_speed).to_dict()
                    for axis in (1, 2, 3)
                ]
            }
        elif args.command == "poincare":
            amplitude = _triplet(args.torque_amplitude)
            angular_frequency = 2.0 * 3.141592653589793 / args.forcing_period
            torque = lambda time, omega, q: (
                amplitude[0] * cos(angular_frequency * time),
                amplitude[1] * sin(angular_frequency * time),
                amplitude[2] * cos(angular_frequency * time),
            )
            payload = stroboscopic_map(
                _model(args),
                _triplet(args.omega),
                forcing_period=args.forcing_period,
                cycles=args.cycles,
                torque=torque,
                damping=args.damping,
            ).to_dict(include_samples=True)
        elif args.command == "atlas":
            payload = atlas_manifest(
                default_atlas_config(
                    inertia_count=args.inertia_count,
                    energy_count=args.energy_count,
                    angular_momentum=args.angular_momentum,
                )
            )
        elif args.command == "benchmark":
            payload = run_oak_benchmarks().to_dict()
        else:
            raise AssertionError(f"unhandled command {args.command}")

        output = getattr(args, "output", None)
        text = json.dumps(payload, indent=2, sort_keys=True)
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0 if payload.get("passed", True) else 2
    except (ArithmeticError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"omega-rigid-body-r02: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
