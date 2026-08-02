from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose, log10
from typing import Any

from .acoustics import screen_rotor_acoustics
from .annular_bem import analyze_annular_bem
from .faults import evaluate_fault_envelope
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .robust_mission import evaluate_robust_mission
from .structural import analyze_blade_structure


@dataclass(frozen=True)
class R03OAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R03OAKReport:
    status: str
    gates: tuple[R03OAKGate, ...]
    physics_certified: bool = False
    model_class: str = "system-screening-structural-robust-acoustic-fault"

    @property
    def passed(self) -> bool:
        return all(gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "passed": self.passed, "physics_certified": self.physics_certified, "model_class": self.model_class, "gates": [gate.to_dict() for gate in self.gates]}


def run_r03_benchmarks() -> R03OAKReport:
    rotor = demo_rotor(); medium = default_air(); mission = demo_air_mission()
    operating = mission.phases[0].operating_point
    aerodynamic = analyze_annular_bem(rotor, medium, operating)
    structural = analyze_blade_structure(rotor, operating, aerodynamic)
    acoustic_10m = screen_rotor_acoustics(rotor, operating, aerodynamic, observer_distance_m=10.0)
    acoustic_20m = screen_rotor_acoustics(rotor, operating, aerodynamic, observer_distance_m=20.0)
    robust = evaluate_robust_mission(rotor, medium, mission)
    faults = evaluate_fault_envelope(rotor, medium, mission)
    motor_out = next(item for item in faults.cases if item.scenario.name == "motor-out")
    blade_loss = next(item for item in faults.cases if item.scenario.name == "single-blade-loss")
    attenuation = acoustic_10m.estimated_overall_spl_db - acoustic_20m.estimated_overall_spl_db
    total_case_weight = sum(item.normalized_weight for item in robust.cases)
    gates = (
        R03OAKGate("annular-input-converged", aerodynamic.converged, f"residual={aerodynamic.maximum_section_residual:.3e}"),
        R03OAKGate("structural-evidence-complete", structural.rotor_mass > 0 and structural.maximum_von_mises_stress >= 0 and structural.minimum_safety_factor > 0 and len(structural.sections) == len(aerodynamic.sections), f"mass={structural.rotor_mass:.6g}, SFmin={structural.minimum_safety_factor:.6g}"),
        R03OAKGate("structural-status-explicit", structural.feasible == (len(structural.violations) == 0), f"feasible={structural.feasible}, violations={structural.violations}"),
        R03OAKGate("blade-passing-frequency-identity", isclose(acoustic_10m.blade_passing_frequency_hz, rotor.blade_count * operating.rpm / 60.0, rel_tol=1e-12), f"BPF={acoustic_10m.blade_passing_frequency_hz:.6g}"),
        R03OAKGate("spherical-distance-attenuation", isclose(attenuation, 20.0 * log10(2.0), rel_tol=1e-12), f"delta={attenuation:.12g} dB"),
        R03OAKGate("robust-case-weights-normalized", isclose(total_case_weight, 1.0, rel_tol=1e-12), f"sum={total_case_weight:.12g}"),
        R03OAKGate("robust-energy-bounded", robust.minimum_shaft_energy_j <= robust.expected_shaft_energy_j <= robust.maximum_shaft_energy_j, f"min={robust.minimum_shaft_energy_j:.6g}, expected={robust.expected_shaft_energy_j:.6g}, max={robust.maximum_shaft_energy_j:.6g}"),
        R03OAKGate("fault-motor-out-detected", not motor_out.mission_feasible and motor_out.minimum_thrust_margin < 0, f"margin={motor_out.minimum_thrust_margin:.6g}"),
        R03OAKGate("blade-loss-dynamic-limit-declared", not blade_loss.safe_continuation_candidate and "unmodeled_rotor_imbalance_and_transient_structural_response" in blade_loss.limitations, f"limitations={blade_loss.limitations}"),
        R03OAKGate("not-physics-certified", not structural.physics_certified and not acoustic_10m.physics_certified and not robust.physics_certified and not faults.physics_certified, "all R0.3 artifacts remain computational screening evidence"),
    )
    passed = all(gate.passed for gate in gates)
    return R03OAKReport("CERTIFIED_COMPUTATIONAL_SYSTEM_SCREENING_R0_3" if passed else "FAILED_R0_3_OAK_GATES", gates)
