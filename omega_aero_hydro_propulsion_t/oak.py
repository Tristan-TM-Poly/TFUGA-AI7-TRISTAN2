from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose
from typing import Any

from .analysis import analyze_rotor
from .cavitation import cavitation_number
from .models import OperatingPoint, default_air, default_water, demo_rotor
from .optimizer import OptimizationConstraints, grid_optimize


@dataclass(frozen=True)
class OAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PropulsionOAKReport:
    status: str
    gates: tuple[OAKGate, ...]
    physics_certified: bool = False
    model_class: str = "low-order-screening"

    @property
    def passed(self) -> bool:
        return all(gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "physics_certified": self.physics_certified,
            "model_class": self.model_class,
            "gates": [gate.to_dict() for gate in self.gates],
        }


def run_propulsion_benchmarks() -> PropulsionOAKReport:
    rotor = demo_rotor()
    air = default_air()
    water = default_water()

    stopped = analyze_rotor(rotor, air, OperatingPoint(20.0, 0.0))
    base = analyze_rotor(rotor, air, OperatingPoint(22.0, 2_200.0))
    denser_air = type(air)(
        name="double-density-test",
        density=2.0 * air.density,
        dynamic_viscosity=2.0 * air.dynamic_viscosity,
        sound_speed=air.sound_speed,
        ambient_pressure=air.ambient_pressure,
    )
    linear_a = analyze_rotor(rotor, air, OperatingPoint(22.0, 2_200.0), max_iterations=0)
    linear_b = analyze_rotor(rotor, denser_air, OperatingPoint(22.0, 2_200.0), max_iterations=0)
    sigma = cavitation_number(
        ambient_pressure=water.ambient_pressure,
        vapor_pressure=water.vapor_pressure or 0.0,
        density=water.density,
        speed=10.0,
    )
    optimization = grid_optimize(
        rotor,
        air,
        OperatingPoint(22.0, 2_200.0),
        diameter_scales=(0.9, 1.0, 1.1),
        chord_scales=(0.9, 1.0),
        pitch_deltas_deg=(-2.0, 0.0, 2.0),
        constraints=OptimizationConstraints(minimum_thrust=1.0, maximum_tip_mach=0.85),
    )

    gates = (
        OAKGate("zero-rpm-zero-load", abs(stopped.thrust) < 1e-12 and abs(stopped.torque) < 1e-12, f"T={stopped.thrust}, Q={stopped.torque}"),
        OAKGate("positive-propulsive-load", base.thrust > 0 and base.torque > 0 and base.shaft_power > 0, f"T={base.thrust:.6g}, P={base.shaft_power:.6g}"),
        OAKGate("uniform-induction-converged", base.converged and base.residual <= 1e-7, f"iterations={base.iterations}, residual={base.residual:.3e}"),
        OAKGate("density-linearity-no-induction", isclose(linear_b.thrust / linear_a.thrust, 2.0, rel_tol=1e-12), f"ratio={linear_b.thrust / linear_a.thrust:.12g}"),
        OAKGate("tip-mach-finite", 0 < base.tip_mach < 1.5, f"M_tip={base.tip_mach:.6g}"),
        OAKGate("cavitation-number-positive", sigma > 0, f"sigma={sigma:.6g}"),
        OAKGate("optimizer-produces-feasible-candidate", optimization.best is not None and optimization.feasible_count > 0, f"feasible={optimization.feasible_count}/{optimization.candidate_count}"),
        OAKGate("not-physics-certified", True, "computational screening only"),
    )
    passed = all(gate.passed for gate in gates)
    return PropulsionOAKReport(
        status="CERTIFIED_COMPUTATIONAL_LOW_ORDER" if passed else "FAILED_OAK_GATES",
        gates=gates,
    )
