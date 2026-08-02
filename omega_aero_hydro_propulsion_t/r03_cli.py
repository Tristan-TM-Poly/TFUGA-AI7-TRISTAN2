from __future__ import annotations

import argparse
import json
from typing import Sequence

from .acoustics import screen_rotor_acoustics
from .annular_bem import analyze_annular_bem
from .faults import evaluate_fault_envelope
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .r03_oak import run_r03_benchmarks
from .robust_mission import evaluate_robust_mission
from .structural import analyze_blade_structure


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-propulsion-r03", description="Ω-PROPULSION R0.3 system screening")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")
    sub.add_parser("structural-demo")
    acoustic = sub.add_parser("acoustic-demo")
    acoustic.add_argument("--distance", type=float, default=10.0)
    sub.add_parser("robust-demo")
    sub.add_parser("fault-demo")
    sub.add_parser("system-demo")
    return parser


def _artifacts(distance: float = 10.0) -> dict[str, object]:
    rotor = demo_rotor(); medium = default_air(); mission = demo_air_mission()
    operating = mission.phases[0].operating_point
    aerodynamic = analyze_annular_bem(rotor, medium, operating)
    return {
        "structural": analyze_blade_structure(rotor, operating, aerodynamic).to_dict(),
        "acoustic": screen_rotor_acoustics(rotor, operating, aerodynamic, observer_distance_m=distance).to_dict(),
        "robust_mission": evaluate_robust_mission(rotor, medium, mission).to_dict(),
        "fault_envelope": evaluate_fault_envelope(rotor, medium, mission).to_dict(),
        "oak": run_r03_benchmarks().to_dict(),
        "epistemic_status": "computational screening only; not flight, marine, structural, acoustic, reliability or regulatory certification",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r03_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2
    artifacts = _artifacts(getattr(args, "distance", 10.0))
    key = {"structural-demo": "structural", "acoustic-demo": "acoustic", "robust-demo": "robust_mission", "fault-demo": "fault_envelope"}.get(args.command)
    payload = artifacts if key is None else {key: artifacts[key], "epistemic_status": artifacts["epistemic_status"]}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
