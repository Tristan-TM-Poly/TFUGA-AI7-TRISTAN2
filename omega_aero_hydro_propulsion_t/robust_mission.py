from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .mission import MissionGenome, MissionPhase, MissionReport, evaluate_mission
from .models import FluidMedium, OperatingPoint, RotorDesign
from .polars import PolarRegistry


@dataclass(frozen=True)
class MissionUncertaintyCase:
    name: str
    density_scale: float = 1.0
    viscosity_scale: float = 1.0
    sound_speed_scale: float = 1.0
    velocity_scale: float = 1.0
    rpm_scale: float = 1.0
    collective_pitch_delta_deg: float = 0.0
    weight: float = 1.0

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("uncertainty case name cannot be empty")
        for name, value in (
            ("density_scale", self.density_scale),
            ("viscosity_scale", self.viscosity_scale),
            ("sound_speed_scale", self.sound_speed_scale),
            ("velocity_scale", self.velocity_scale),
            ("rpm_scale", self.rpm_scale),
            ("weight", self.weight),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RobustMissionCaseResult:
    case: MissionUncertaintyCase
    normalized_weight: float
    report: MissionReport

    def to_dict(self) -> dict[str, Any]:
        return {"case": self.case.to_dict(), "normalized_weight": self.normalized_weight, "report": self.report.to_dict()}


@dataclass(frozen=True)
class RobustMissionReport:
    mission_name: str
    design_name: str
    expected_shaft_energy_j: float
    minimum_shaft_energy_j: float
    maximum_shaft_energy_j: float
    expected_mission_efficiency: float
    worst_mission_efficiency: float
    maximum_tip_mach: float
    feasible_probability: float
    robust_feasible: bool
    cases: tuple[RobustMissionCaseResult, ...]
    model: str = "deterministic-weighted-uncertainty-corners-r0.3"
    physics_certified: bool = False
    certification_notice: str = "screening over declared cases only; not a complete probabilistic safety, weather or reliability analysis"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_name": self.mission_name, "design_name": self.design_name,
            "expected_shaft_energy_j": self.expected_shaft_energy_j,
            "minimum_shaft_energy_j": self.minimum_shaft_energy_j,
            "maximum_shaft_energy_j": self.maximum_shaft_energy_j,
            "expected_mission_efficiency": self.expected_mission_efficiency,
            "worst_mission_efficiency": self.worst_mission_efficiency,
            "maximum_tip_mach": self.maximum_tip_mach,
            "feasible_probability": self.feasible_probability,
            "robust_feasible": self.robust_feasible,
            "cases": [item.to_dict() for item in self.cases],
            "model": self.model, "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def default_uncertainty_cases() -> tuple[MissionUncertaintyCase, ...]:
    return (
        MissionUncertaintyCase("nominal", weight=4.0),
        MissionUncertaintyCase("hot-low-density", density_scale=0.88, viscosity_scale=1.08, sound_speed_scale=1.04),
        MissionUncertaintyCase("cold-dense", density_scale=1.12, viscosity_scale=0.92, sound_speed_scale=0.96),
        MissionUncertaintyCase("headwind-and-rpm-derate", velocity_scale=1.12, rpm_scale=0.95, collective_pitch_delta_deg=1.0),
        MissionUncertaintyCase("tailwind-and-control-bias", velocity_scale=0.90, rpm_scale=1.02, collective_pitch_delta_deg=-1.0),
    )


def _transform_medium(medium: FluidMedium, case: MissionUncertaintyCase) -> FluidMedium:
    return FluidMedium(
        f"{medium.name}:{case.name}", medium.density * case.density_scale,
        medium.dynamic_viscosity * case.viscosity_scale,
        medium.sound_speed * case.sound_speed_scale,
        medium.ambient_pressure, medium.vapor_pressure,
    )


def _transform_mission(mission: MissionGenome, case: MissionUncertaintyCase) -> MissionGenome:
    phases = tuple(MissionPhase(
        phase.name, phase.duration_s,
        OperatingPoint(
            phase.operating_point.freestream_velocity * case.velocity_scale,
            phase.operating_point.rpm * case.rpm_scale,
            phase.operating_point.collective_pitch_deg + case.collective_pitch_delta_deg,
        ),
        phase.minimum_thrust, phase.maximum_shaft_power, phase.maximum_tip_mach,
        phase.importance_weight,
    ) for phase in mission.phases)
    return MissionGenome.from_phases(
        name=f"{mission.name}:{case.name}", domain=mission.domain, vehicle=mission.vehicle,
        phases=phases, objectives=mission.objectives,
        provenance=f"{mission.provenance}; uncertainty case={case.name}",
    )


def evaluate_robust_mission(
    design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    *,
    cases: Iterable[MissionUncertaintyCase] | None = None,
    registry: PolarRegistry | None = None,
) -> RobustMissionReport:
    design.validate(); medium.validate(); mission.validate()
    selected = tuple(cases or default_uncertainty_cases())
    if not selected:
        raise ValueError("at least one uncertainty case is required")
    names: set[str] = set()
    for case in selected:
        case.validate()
        if case.name in names:
            raise ValueError("uncertainty case names must be unique")
        names.add(case.name)
    total_weight = sum(case.weight for case in selected)
    results = tuple(RobustMissionCaseResult(
        case, case.weight / total_weight,
        evaluate_mission(design, _transform_medium(medium, case), _transform_mission(mission, case), registry=registry),
    ) for case in selected)
    energies = [item.report.total_shaft_energy_j for item in results]
    efficiencies = [item.report.mission_efficiency for item in results]
    return RobustMissionReport(
        mission.name, design.name,
        sum(item.normalized_weight * item.report.total_shaft_energy_j for item in results),
        min(energies), max(energies),
        sum(item.normalized_weight * item.report.mission_efficiency for item in results),
        min(efficiencies), max(item.report.maximum_tip_mach for item in results),
        sum(item.normalized_weight for item in results if item.report.feasible),
        all(item.report.feasible for item in results), results,
    )
