from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from .architecture_compiler import compile_propulsion_architectures
from .evidence_ladder import assess_evidence_ladder, computational_receipts
from .models import OperatingPoint, default_air, default_water, demo_rotor
from .r05_oak import demo_air_intent, demo_water_intent, run_r05_benchmarks
from .wake_graph import WakeConfig, analyze_wake_graph


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-propulsion-r05",
        description="Ω-PROPULSION R0.5 WakeGraph, architecture compiler and evidence ladder",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")

    wake = sub.add_parser("wake-demo")
    wake.add_argument("--rpm", type=float, default=2_200.0)
    wake.add_argument("--velocity", type=float, default=22.0)
    wake.add_argument("--revolutions", type=float, default=1.5)
    wake.add_argument("--segments-per-revolution", type=int, default=24)
    wake.add_argument("--summary-only", action="store_true")

    architecture = sub.add_parser("architecture-demo")
    architecture.add_argument("--domain", choices=("air", "water"), default="air")

    sub.add_parser("evidence-demo")
    return parser


def _wake_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "design_name": payload["design_name"],
        "medium_name": payload["medium_name"],
        "model": payload["model"],
        "filament_count": payload["filament_count"],
        "segment_count": len(payload["segments"]),
        "node_count": len(payload["nodes"]),
        "total_segment_length": payload["total_segment_length"],
        "circulation_l1": payload["circulation_l1"],
        "maximum_probe_speed": payload["maximum_probe_speed"],
        "probes": payload["probes"],
        "evidence_hash": payload["evidence_hash"],
        "physical_fidelity_claim": payload["physical_fidelity_claim"],
        "physics_certified": payload["physics_certified"],
        "limitations": payload["limitations"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r05_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    if args.command == "wake-demo":
        report = analyze_wake_graph(
            demo_rotor(),
            default_air(),
            OperatingPoint(
                freestream_velocity=args.velocity,
                rpm=args.rpm,
                collective_pitch_deg=0.0,
            ),
            config=WakeConfig(
                revolutions=args.revolutions,
                segments_per_revolution=args.segments_per_revolution,
            ),
        )
        payload = report.to_dict()
        print(json.dumps(_wake_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0

    if args.command == "architecture-demo":
        if args.domain == "air":
            report = compile_propulsion_architectures(demo_air_intent(), default_air())
        else:
            report = compile_propulsion_architectures(demo_water_intent(), default_water())
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    wake = analyze_wake_graph(
        demo_rotor(),
        default_air(),
        OperatingPoint(freestream_velocity=22.0, rpm=2_200.0),
        config=WakeConfig(revolutions=1.0, segments_per_revolution=16),
    )
    report = assess_evidence_ladder(computational_receipts(wake_hash=wake.evidence_hash))
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
