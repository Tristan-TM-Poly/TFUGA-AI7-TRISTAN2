from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omega_cyber_physical_systems_t.cosim import demo_nominal_scenario, run_closed_loop_axis
from omega_cyber_physical_systems_t.energy_graph import audit_closed_loop_energy
from omega_cyber_physical_systems_t.models import demo_electromechanical_axis_blueprint
from omega_cyber_physical_systems_t.r02_oak import run_cps_r02_benchmarks
from omega_cyber_physical_systems_t.unit_graph import audit_blueprint_units, default_unit_registry


def main() -> None:
    blueprint = demo_electromechanical_axis_blueprint()
    unit_report = audit_blueprint_units(blueprint)
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    energy_report = audit_closed_loop_energy(simulation)
    adversarial_report = audit_closed_loop_energy(simulation, untracked_output_energy_j=5.0)
    registry = default_unit_registry()
    oak = run_cps_r02_benchmarks()
    print(
        json.dumps(
            {
                "unit_graph": {
                    "system_id": unit_report.system_id,
                    "dimensionally_valid": unit_report.dimensionally_valid,
                    "causal_connections_valid": unit_report.causal_connections_valid,
                    "warning_count": unit_report.warning_count,
                    "power_conjugate_port_count": unit_report.power_conjugate_port_count,
                    "direct_power_port_count": unit_report.direct_power_port_count,
                    "evidence_hash": unit_report.evidence_hash,
                },
                "energy_graph": {
                    "scenario_id": energy_report.scenario_id,
                    "sample_count": energy_report.sample_count,
                    "balance_passed": energy_report.balance_passed,
                    "global_residual_j": energy_report.global_residual_j,
                    "global_normalized_residual": energy_report.global_normalized_residual,
                    "passivity_classification": energy_report.passivity.classification,
                    "evidence_hash": energy_report.evidence_hash,
                },
                "adversarial_probe": {
                    "untracked_output_energy_j": 5.0,
                    "global_balance_passed": adversarial_report.balance("global").passed,
                    "global_residual_j": adversarial_report.global_residual_j,
                    "evidence_hash": adversarial_report.evidence_hash,
                },
                "unit_conversion": {
                    "60_rpm_in_rad_s": registry.convert(60.0, "rpm", "rad/s"),
                    "60_L_min_in_m3_s": registry.convert(60.0, "L/min", "m^3/s"),
                },
                "oak": oak.to_dict(),
                "epistemic_status": (
                    "deterministic dimensional and lumped-energy accounting only; "
                    "not experimental proof, passivity proof or hardware certification"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
