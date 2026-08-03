"""CLI for Ω-SPACE-HG-T∞ R0.2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .r02 import (
    canonical_attitude_case,
    canonical_inclined_orbit,
    canonical_perturbation_config,
    run_r02_oak_benchmarks,
    simulate_r02_attitude,
    simulate_r02_orbit,
)


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-space-hg-r02")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="emit canonical R0.2 orbit and attitude fixtures")
    manifest.add_argument("--output")

    orbit = commands.add_parser("orbit", help="run J2 plus optional drag/SRP propagation")
    orbit.add_argument("--duration-orbits", type=float, default=10.0)
    orbit.add_argument("--step-s", type=float, default=20.0)
    orbit.add_argument("--drag", action="store_true")
    orbit.add_argument("--srp", action="store_true")
    orbit.add_argument("--output")

    attitude = commands.add_parser("attitude", help="run deterministic closed-loop quaternion attitude simulation")
    attitude.add_argument("--duration-s", type=float, default=120.0)
    attitude.add_argument("--step-s", type=float, default=0.2)
    attitude.add_argument("--ideal-sensors", action="store_true")
    attitude.add_argument("--output")

    oak = commands.add_parser("oak", help="run R0.2 OAKBench")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "manifest":
        initial, target, controller = canonical_attitude_case()
        payload = {
            "release": "R0.2",
            "orbit": canonical_inclined_orbit().to_dict(),
            "perturbations": canonical_perturbation_config().to_dict(),
            "attitude": {
                "initial": initial.to_dict(),
                "target_quaternion": target,
                "controller": {
                    "inertia_kg_m2": controller.inertia_kg_m2,
                    "kp_n_m_per_quaternion": controller.kp_n_m_per_quaternion,
                    "kd_n_m_s": controller.kd_n_m_s,
                    "max_wheel_torque_n_m": controller.max_wheel_torque_n_m,
                    "max_wheel_momentum_nms": controller.max_wheel_momentum_nms,
                    "wheel_friction_per_s": controller.wheel_friction_per_s,
                },
            },
            "flight_qualified_claimed": False,
        }
    elif arguments.command == "orbit":
        payload = simulate_r02_orbit(
            duration_orbits=arguments.duration_orbits,
            step_s=arguments.step_s,
            include_drag=arguments.drag,
            include_srp=arguments.srp,
        )
    elif arguments.command == "attitude":
        payload = simulate_r02_attitude(
            duration_s=arguments.duration_s,
            step_s=arguments.step_s,
            sensor_noise=not arguments.ideal_sensors,
        )
    elif arguments.command == "oak":
        payload = run_r02_oak_benchmarks()
    else:
        raise AssertionError("unreachable")
    _emit(payload, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
