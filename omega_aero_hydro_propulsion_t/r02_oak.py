from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose
from typing import Any

from .annular_bem import analyze_annular_bem
from .mission import demo_air_mission, evaluate_mission
from .models import BladeStation, OperatingPoint, RotorDesign, default_air, demo_rotor
from .polars import PolarRegistry, PolarSample, PolarTable, demo_polar_table


@dataclass(frozen=True)
class R02OAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R02OAKReport:
    status: str
    gates: tuple[R02OAKGate, ...]
    physics_certified: bool = False
    model_class: str = "annular-bem-tabulated-polars-multipoint-mission"

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


def run_r02_benchmarks() -> R02OAKReport:
    table = PolarTable.from_samples(
        "oak-linear-fixture",
        (
            PolarSample(0.0, 100_000.0, 0.10, 0.0, 0.010),
            PolarSample(10.0, 100_000.0, 0.10, 1.0, 0.050),
            PolarSample(0.0, 500_000.0, 0.20, 0.0, 0.009),
            PolarSample(10.0, 500_000.0, 0.20, 1.1, 0.040),
        ),
        source_type="deterministic-test-fixture",
        provenance="OAK R0.2 regression fixture",
    )
    exact = table.evaluate(5.0, reynolds=100_000.0, mach=0.10)
    registry = PolarRegistry([demo_polar_table()])
    base = demo_rotor()
    tabulated_design = RotorDesign(
        name="oak-tabulated-demo",
        blade_count=base.blade_count,
        hub_radius=base.hub_radius,
        tip_radius=base.tip_radius,
        stations=tuple(
            BladeStation(station.radius, station.chord, station.twist_deg, "demo-tabulated-symmetric")
            for station in base.stations
        ),
    )
    analytic = analyze_annular_bem(base, default_air(), OperatingPoint(22.0, 2_200.0))
    tabulated = analyze_annular_bem(
        tabulated_design,
        default_air(),
        OperatingPoint(22.0, 2_200.0),
        registry=registry,
    )
    mission_report = evaluate_mission(base, default_air(), demo_air_mission())
    summed_energy = sum(phase.shaft_energy_j for phase in mission_report.phases)

    gates = (
        R02OAKGate(
            "polar-alpha-interpolation",
            isclose(exact.lift_coefficient, 0.5, rel_tol=0.0, abs_tol=1e-12),
            f"Cl(5deg)={exact.lift_coefficient:.12g}",
        ),
        R02OAKGate(
            "polar-provenance-retained",
            table.provenance == "OAK R0.2 regression fixture" and table.source_type.startswith("deterministic"),
            f"source={table.source_type}, provenance={table.provenance}",
        ),
        R02OAKGate(
            "annular-bem-convergence",
            analytic.converged and analytic.maximum_section_residual <= 1e-6,
            f"residual={analytic.maximum_section_residual:.3e}",
        ),
        R02OAKGate(
            "annular-positive-load",
            analytic.thrust > 0 and analytic.torque > 0 and analytic.shaft_power > 0,
            f"T={analytic.thrust:.6g}, Q={analytic.torque:.6g}, P={analytic.shaft_power:.6g}",
        ),
        R02OAKGate(
            "tabulated-polar-dispatch",
            tabulated.converged and all(section.polar_model.startswith("tabulated") for section in tabulated.sections),
            f"models={sorted({section.polar_model for section in tabulated.sections})}",
        ),
        R02OAKGate(
            "mission-three-phase-complete",
            len(mission_report.phases) == 3 and mission_report.feasible,
            f"phases={len(mission_report.phases)}, feasible={mission_report.feasible}",
        ),
        R02OAKGate(
            "mission-energy-accounting",
            isclose(mission_report.total_shaft_energy_j, summed_energy, rel_tol=1e-12),
            f"energy={mission_report.total_shaft_energy_j:.6g} J",
        ),
        R02OAKGate(
            "mission-efficiency-bounded",
            0.0 <= mission_report.mission_efficiency <= 1.0,
            f"eta_mission={mission_report.mission_efficiency:.6g}",
        ),
        R02OAKGate(
            "not-physics-certified",
            not analytic.physics_certified and "not flight" in mission_report.certification_notice,
            mission_report.certification_notice,
        ),
    )
    passed = all(gate.passed for gate in gates)
    return R02OAKReport(
        status="CERTIFIED_COMPUTATIONAL_MULTIPOINT_R0_2" if passed else "FAILED_R0_2_OAK_GATES",
        gates=gates,
    )
