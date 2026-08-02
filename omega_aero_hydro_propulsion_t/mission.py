from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .annular_bem import AnnularBEMAnalysis, analyze_annular_bem
from .models import FluidMedium, OperatingPoint, RotorDesign
from .polars import PolarRegistry


@dataclass(frozen=True)
class MissionPhase:
    name: str
    duration_s: float
    operating_point: OperatingPoint
    minimum_thrust: float = 0.0
    maximum_shaft_power: float | None = None
    maximum_tip_mach: float | None = None
    importance_weight: float = 1.0

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("mission phase name cannot be empty")
        if self.duration_s <= 0 or self.minimum_thrust < 0 or self.importance_weight <= 0:
            raise ValueError("invalid mission phase duration, thrust or weight")
        if self.maximum_shaft_power is not None and self.maximum_shaft_power <= 0:
            raise ValueError("maximum_shaft_power must be positive")
        if self.maximum_tip_mach is not None and self.maximum_tip_mach <= 0:
            raise ValueError("maximum_tip_mach must be positive")
        self.operating_point.validate()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operating_point"] = self.operating_point.to_dict()
        return payload


@dataclass(frozen=True)
class MissionGenome:
    name: str
    domain: str
    vehicle: str
    phases: tuple[MissionPhase, ...]
    objectives: tuple[str, ...] = ("minimize_energy", "maximize_efficiency")
    provenance: str = "user-defined research mission"

    @classmethod
    def from_phases(
        cls,
        *,
        name: str,
        domain: str,
        vehicle: str,
        phases: Iterable[MissionPhase],
        objectives: Iterable[str] = ("minimize_energy", "maximize_efficiency"),
        provenance: str = "user-defined research mission",
    ) -> "MissionGenome":
        mission = cls(name, domain, vehicle, tuple(phases), tuple(objectives), provenance)
        mission.validate()
        return mission

    def validate(self) -> None:
        if not self.name.strip() or not self.domain.strip() or not self.vehicle.strip():
            raise ValueError("mission name, domain and vehicle are required")
        if not self.phases:
            raise ValueError("at least one mission phase is required")
        names: set[str] = set()
        for phase in self.phases:
            phase.validate()
            if phase.name in names:
                raise ValueError("mission phase names must be unique")
            names.add(phase.name)
        if not self.objectives or any(not item.strip() for item in self.objectives):
            raise ValueError("at least one non-empty mission objective is required")
        if not self.provenance.strip():
            raise ValueError("mission provenance is required")

    @property
    def duration_s(self) -> float:
        return sum(phase.duration_s for phase in self.phases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "vehicle": self.vehicle,
            "duration_s": self.duration_s,
            "objectives": list(self.objectives),
            "provenance": self.provenance,
            "phases": [phase.to_dict() for phase in self.phases],
        }


@dataclass(frozen=True)
class MissionPhaseResult:
    phase: MissionPhase
    analysis: AnnularBEMAnalysis
    shaft_energy_j: float
    useful_propulsive_energy_j: float
    feasible: bool
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.to_dict(),
            "analysis": self.analysis.to_dict(),
            "shaft_energy_j": self.shaft_energy_j,
            "useful_propulsive_energy_j": self.useful_propulsive_energy_j,
            "feasible": self.feasible,
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class MissionReport:
    mission_name: str
    design_name: str
    total_shaft_energy_j: float
    total_useful_propulsive_energy_j: float
    mission_efficiency: float
    weighted_efficiency: float
    maximum_tip_mach: float
    feasible: bool
    phases: tuple[MissionPhaseResult, ...]
    model: str = "multipoint-annular-bem-mission-r0.2"
    certification_notice: str = "research screening only; not flight or marine certification"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_name": self.mission_name,
            "design_name": self.design_name,
            "total_shaft_energy_j": self.total_shaft_energy_j,
            "total_useful_propulsive_energy_j": self.total_useful_propulsive_energy_j,
            "mission_efficiency": self.mission_efficiency,
            "weighted_efficiency": self.weighted_efficiency,
            "maximum_tip_mach": self.maximum_tip_mach,
            "feasible": self.feasible,
            "model": self.model,
            "certification_notice": self.certification_notice,
            "phases": [phase.to_dict() for phase in self.phases],
        }


def _phase_violations(phase: MissionPhase, analysis: AnnularBEMAnalysis) -> tuple[str, ...]:
    violations: list[str] = []
    if analysis.thrust < phase.minimum_thrust:
        violations.append("minimum_thrust")
    if phase.maximum_shaft_power is not None and analysis.shaft_power > phase.maximum_shaft_power:
        violations.append("maximum_shaft_power")
    if phase.maximum_tip_mach is not None and analysis.tip_mach > phase.maximum_tip_mach:
        violations.append("maximum_tip_mach")
    if not analysis.converged:
        violations.append("annular_bem_convergence")
    if analysis.shaft_power < 0:
        violations.append("negative_shaft_power")
    return tuple(violations)


def evaluate_mission(
    design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    *,
    registry: PolarRegistry | None = None,
) -> MissionReport:
    design.validate()
    medium.validate()
    mission.validate()
    results: list[MissionPhaseResult] = []
    for phase in mission.phases:
        analysis = analyze_annular_bem(design, medium, phase.operating_point, registry=registry)
        shaft_energy = max(0.0, analysis.shaft_power) * phase.duration_s
        useful_energy = max(0.0, analysis.thrust * phase.operating_point.freestream_velocity) * phase.duration_s
        violations = _phase_violations(phase, analysis)
        results.append(
            MissionPhaseResult(
                phase=phase,
                analysis=analysis,
                shaft_energy_j=shaft_energy,
                useful_propulsive_energy_j=useful_energy,
                feasible=not violations,
                violations=violations,
            )
        )
    total_shaft = sum(result.shaft_energy_j for result in results)
    total_useful = sum(result.useful_propulsive_energy_j for result in results)
    total_weight = sum(result.phase.importance_weight for result in results)
    weighted_efficiency = sum(
        result.phase.importance_weight * result.analysis.propulsive_efficiency for result in results
    ) / total_weight
    return MissionReport(
        mission_name=mission.name,
        design_name=design.name,
        total_shaft_energy_j=total_shaft,
        total_useful_propulsive_energy_j=total_useful,
        mission_efficiency=total_useful / total_shaft if total_shaft > 0 else 0.0,
        weighted_efficiency=weighted_efficiency,
        maximum_tip_mach=max(result.analysis.tip_mach for result in results),
        feasible=all(result.feasible for result in results),
        phases=tuple(results),
    )


def demo_air_mission() -> MissionGenome:
    return MissionGenome.from_phases(
        name="electric-propeller-three-phase-demo",
        domain="aerial",
        vehicle="electric-research-aircraft",
        phases=(
            MissionPhase(
                "takeoff",
                45.0,
                OperatingPoint(12.0, 2_600.0, 3.0),
                minimum_thrust=40.0,
                maximum_shaft_power=30_000.0,
                maximum_tip_mach=0.75,
                importance_weight=2.0,
            ),
            MissionPhase(
                "climb",
                240.0,
                OperatingPoint(28.0, 2_350.0, 1.0),
                minimum_thrust=25.0,
                maximum_shaft_power=25_000.0,
                maximum_tip_mach=0.75,
                importance_weight=1.5,
            ),
            MissionPhase(
                "cruise",
                1_800.0,
                OperatingPoint(35.0, 2_300.0, 4.0),
                minimum_thrust=12.0,
                maximum_shaft_power=18_000.0,
                maximum_tip_mach=0.72,
                importance_weight=3.0,
            ),
        ),
        provenance="deterministic demonstration mission; not an aircraft requirement set",
    )
