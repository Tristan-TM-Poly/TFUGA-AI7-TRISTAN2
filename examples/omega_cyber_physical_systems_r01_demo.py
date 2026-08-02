from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from omega_cyber_physical_systems_t.compiler import compile_prototype, demo_integrated_robot_intent
from omega_cyber_physical_systems_t.cosim import demo_fault_scenario, demo_nominal_scenario, run_closed_loop_axis
from omega_cyber_physical_systems_t.fault_analysis import analyze_fault_propagation
from omega_cyber_physical_systems_t.models import demo_electromechanical_axis_blueprint


def _summary(report):
    return {
        "scenario": report.scenario.scenario_id,
        "samples": len(report.samples),
        "final_position_m": report.final_position_m,
        "final_error_m": report.final_error_m,
        "rms_error_m": report.rms_error_m,
        "peak_current_a": report.peak_current_a,
        "peak_temperature_k": report.peak_temperature_k,
        "deadline_miss_count": report.deadline_miss_count,
        "shutdown_reasons": list(report.shutdown_reasons),
        "evidence_hash": report.evidence_hash,
        "physics_certified": report.physics_certified,
        "hardware_validated": report.hardware_validated,
    }


def main() -> None:
    blueprint = demo_electromechanical_axis_blueprint()
    nominal = run_closed_loop_axis(demo_nominal_scenario())
    faulted = run_closed_loop_axis(demo_fault_scenario())
    compilation = compile_prototype(demo_integrated_robot_intent())
    faults = analyze_fault_propagation(blueprint)
    print(
        json.dumps(
            {
                "blueprint": {
                    "system_id": blueprint.system_id,
                    "component_count": len(blueprint.components),
                    "connection_count": len(blueprint.connections),
                    "domains": list(blueprint.domains),
                    "evidence_hash": blueprint.evidence_hash,
                },
                "nominal_cosim": _summary(nominal),
                "faulted_cosim": _summary(faulted),
                "compiled_prototype": {
                    "intent_id": compilation.intent.intent_id,
                    "eligible_count": compilation.eligible_count,
                    "best": None if compilation.best is None else compilation.best.architecture.architecture_id,
                    "evidence_hash": compilation.evidence_hash,
                    "engineering_recommendation": compilation.engineering_recommendation,
                },
                "fault_analysis": {
                    "record_count": len(faults.records),
                    "highest_rpn": faults.highest_rpn,
                    "single_point_risk_count": faults.single_point_risk_count,
                    "heuristic_resilience_score": faults.heuristic_resilience_score,
                    "evidence_hash": faults.evidence_hash,
                    "safety_certified": faults.safety_certified,
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
