from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .compiler import compile_prototype, demo_integrated_robot_intent
from .cosim import demo_fault_scenario, demo_nominal_scenario, run_closed_loop_axis
from .dynamics import dc_motor_model, mass_spring_damper_model, simulate_state_space
from .evidence import assess_evidence_ledger, computational_demo_receipts
from .fault_analysis import analyze_fault_propagation
from .inventory import InventoryConfig, discover_repository_systems, summarize_inventory
from .models import demo_electromechanical_axis_blueprint
from .oak import run_cps_benchmarks


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-cps",
        description="Ω-CYBER-PHYSICAL-SYSTEMS-T whole-system mechanics/electrical/electronics/software research OS",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")
    sub.add_parser("blueprint-demo")
    sub.add_parser("compiler-demo")
    sub.add_parser("fault-demo")
    sub.add_parser("evidence-demo")

    dynamics = sub.add_parser("dynamics-demo")
    dynamics.add_argument("--model", choices=("mechanical", "motor"), default="mechanical")
    dynamics.add_argument("--summary-only", action="store_true")

    cosim = sub.add_parser("cosim-demo")
    cosim.add_argument("--faulted", action="store_true")
    cosim.add_argument("--summary-only", action="store_true")

    inventory = sub.add_parser("inventory")
    inventory.add_argument("--root", default=".")
    inventory.add_argument("--max-files-per-system", type=int, default=256)
    inventory.add_argument("--max-bytes-per-file", type=int, default=128_000)
    inventory.add_argument("--summary-only", action="store_true")
    return parser


def _trace_summary(payload: dict[str, Any]) -> dict[str, Any]:
    last = payload["samples"][-1]
    return {
        "model_id": payload["model_id"],
        "dt_s": payload["dt_s"],
        "sample_count": len(payload["samples"]),
        "final_state": last["state"],
        "final_outputs": last["outputs"],
        "finite": payload["finite"],
        "evidence_hash": payload["evidence_hash"],
        "physics_certified": payload["physics_certified"],
    }


def _cosim_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": payload["scenario"]["scenario_id"],
        "sample_count": payload["sample_count"],
        "final_position_m": payload["final_position_m"],
        "final_error_m": payload["final_error_m"],
        "rms_error_m": payload["rms_error_m"],
        "overshoot_fraction": payload["overshoot_fraction"],
        "settling_time_s": payload["settling_time_s"],
        "peak_current_a": payload["peak_current_a"],
        "peak_temperature_k": payload["peak_temperature_k"],
        "absolute_electrical_energy_j": payload["absolute_electrical_energy_j"],
        "positive_mechanical_energy_j": payload["positive_mechanical_energy_j"],
        "deadline_miss_count": payload["deadline_miss_count"],
        "saturation_count": payload["saturation_count"],
        "shutdown_reasons": payload["shutdown_reasons"],
        "finite": payload["finite"],
        "evidence_hash": payload["evidence_hash"],
        "physics_certified": payload["physics_certified"],
        "software_certified": payload["software_certified"],
        "hardware_validated": payload["hardware_validated"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_cps_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    blueprint = demo_electromechanical_axis_blueprint()
    if args.command == "blueprint-demo":
        print(json.dumps(blueprint.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "compiler-demo":
        report = compile_prototype(demo_integrated_robot_intent())
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "fault-demo":
        report = analyze_fault_propagation(blueprint)
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "evidence-demo":
        simulation = run_closed_loop_axis(demo_nominal_scenario())
        import hashlib

        test_hash = hashlib.sha256(b"omega-cps-r0.1-cli-demo").hexdigest()
        receipts = computational_demo_receipts(
            blueprint_hash=blueprint.evidence_hash,
            simulation_hash=simulation.evidence_hash,
            test_definition_hash=test_hash,
            test_count=1,
        )
        report = assess_evidence_ledger(receipts)
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "dynamics-demo":
        if args.model == "mechanical":
            model = mass_spring_damper_model(mass_kg=2.0, damping_n_s_m=1.5, stiffness_n_m=8.0)
            trace = simulate_state_space(
                model,
                initial_state=(0.0, 0.0),
                input_sequence=((3.0,),) * 200,
                dt_s=0.002,
            )
        else:
            model = dc_motor_model(
                resistance_ohm=1.2,
                inductance_h=0.01,
                torque_constant_nm_a=0.08,
                back_emf_v_s_rad=0.08,
                inertia_kg_m2=0.004,
                viscous_friction_nm_s_rad=0.002,
            )
            trace = simulate_state_space(
                model,
                initial_state=(0.0, 0.0),
                input_sequence=((12.0, 0.02),) * 300,
                dt_s=0.001,
            )
        payload = trace.to_dict()
        print(json.dumps(_trace_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0

    if args.command == "cosim-demo":
        report = run_closed_loop_axis(demo_fault_scenario() if args.faulted else demo_nominal_scenario())
        payload = report.to_dict()
        print(json.dumps(_cosim_summary(payload) if args.summary_only else payload, indent=2, sort_keys=True))
        return 0

    report = discover_repository_systems(
        Path(args.root),
        config=InventoryConfig(
            max_files_per_system=args.max_files_per_system,
            max_bytes_per_file=args.max_bytes_per_file,
        ),
    )
    payload = summarize_inventory(report) if args.summary_only else report.to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
