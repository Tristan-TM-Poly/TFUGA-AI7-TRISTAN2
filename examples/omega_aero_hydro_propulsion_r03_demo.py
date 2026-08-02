from __future__ import annotations

import json

from omega_aero_hydro_propulsion_t.acoustics import screen_rotor_acoustics
from omega_aero_hydro_propulsion_t.annular_bem import analyze_annular_bem
from omega_aero_hydro_propulsion_t.faults import evaluate_fault_envelope
from omega_aero_hydro_propulsion_t.mission import demo_air_mission
from omega_aero_hydro_propulsion_t.models import default_air, demo_rotor
from omega_aero_hydro_propulsion_t.r03_oak import run_r03_benchmarks
from omega_aero_hydro_propulsion_t.robust_mission import evaluate_robust_mission
from omega_aero_hydro_propulsion_t.structural import analyze_blade_structure


def main() -> None:
    rotor = demo_rotor(); medium = default_air(); mission = demo_air_mission()
    operating = mission.phases[0].operating_point
    aerodynamic = analyze_annular_bem(rotor, medium, operating)
    print(json.dumps({
        "structural": analyze_blade_structure(rotor, operating, aerodynamic).to_dict(),
        "acoustic": screen_rotor_acoustics(rotor, operating, aerodynamic).to_dict(),
        "robust_mission": evaluate_robust_mission(rotor, medium, mission).to_dict(),
        "fault_envelope": evaluate_fault_envelope(rotor, medium, mission).to_dict(),
        "oak": run_r03_benchmarks().to_dict(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
