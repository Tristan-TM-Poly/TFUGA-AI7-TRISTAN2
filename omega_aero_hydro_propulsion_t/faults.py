from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .annular_bem import analyze_annular_bem
from .mission import MissionGenome
from .models import FluidMedium, OperatingPoint, RotorDesign
from .polars import PolarRegistry


@dataclass(frozen=True)
class FaultScenario:
    name: str
    rpm_scale: float = 1.0
    collective_pitch_delta_deg: float = 0.0
    blade_count_delta: int = 0
    available_power_scale: float = 1.0
    requires_dynamic_balance_model: bool = False
    severity: str = "minor"

    def validate(self) -> None:
        if not self.name.strip() or not self.severity.strip():
            raise ValueError("fault name and severity are required")
        if self.rpm_scale < 0:
            raise ValueError("rpm_scale cannot be negative")
        if not 0 < self.available_power_scale <= 1:
            raise ValueError("available_power_scale must lie in (0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FaultPhaseResult:
    phase_name: str
    thrust: float
    shaft_power: float
    tip_mach: float
    thrust_margin: float
    power_margin: float | None
    feasible: bool
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FaultCaseResult:
    scenario: FaultScenario
    effective_blade_count: int
    mission_feasible: bool
    safe_continuation_candidate: bool
    minimum_thrust_margin: float
    minimum_power_margin: float | None
    maximum_tip_mach: float
    phases: tuple[FaultPhaseResult, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.to_dict(), "effective_blade_count": self.effective_blade_count,
            "mission_feasible": self.mission_feasible,
            "safe_continuation_candidate": self.safe_continuation_candidate,
            "minimum_thrust_margin": self.minimum_thrust_margin,
            "minimum_power_margin": self.minimum_power_margin,
            "maximum_tip_mach": self.maximum_tip_mach,
            "phases": [phase.to_dict() for phase in self.phases],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class FaultEnvelopeReport:
    mission_name: str
    design_name: str
    case_count: int
    feasible_case_fraction: float
    safe_continuation_fraction: float
    critical_scenario: str
    cases: tuple[FaultCaseResult, ...]
    model: str = "deterministic-fault-envelope-r0.3"
    physics_certified: bool = False
    certification_notice: str = "fault screening only; imbalance, transients, containment and vehicle dynamics require dedicated models and tests"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_name": self.mission_name, "design_name": self.design_name,
            "case_count": self.case_count, "feasible_case_fraction": self.feasible_case_fraction,
            "safe_continuation_fraction": self.safe_continuation_fraction,
            "critical_scenario": self.critical_scenario,
            "cases": [case.to_dict() for case in self.cases],
            "model": self.model, "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def default_fault_scenarios() -> tuple[FaultScenario, ...]:
    return (
        FaultScenario("rpm-derate-10pct", rpm_scale=0.90, available_power_scale=0.82, severity="minor"),
        FaultScenario("pitch-jam-minus-4deg", collective_pitch_delta_deg=-4.0, severity="major"),
        FaultScenario("single-blade-loss", blade_count_delta=-1, available_power_scale=0.70, requires_dynamic_balance_model=True, severity="hazardous"),
        FaultScenario("motor-out", rpm_scale=0.0, available_power_scale=0.01, severity="hazardous"),
    )


def evaluate_fault_envelope(
    design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    *,
    scenarios: Iterable[FaultScenario] | None = None,
    registry: PolarRegistry | None = None,
) -> FaultEnvelopeReport:
    design.validate(); medium.validate(); mission.validate()
    selected = tuple(scenarios or default_fault_scenarios())
    if not selected:
        raise ValueError("at least one fault scenario is required")
    names: set[str] = set()
    for scenario in selected:
        scenario.validate()
        if scenario.name in names:
            raise ValueError("fault scenario names must be unique")
        names.add(scenario.name)
    cases: list[FaultCaseResult] = []
    for scenario in selected:
        blade_count = design.blade_count + scenario.blade_count_delta
        if blade_count < 1:
            raise ValueError("fault scenario removes every blade; use motor-out for zero-thrust screening")
        fault_design = RotorDesign(f"{design.name}:{scenario.name}", blade_count, design.hub_radius, design.tip_radius, design.stations)
        limitations = ["unmodeled_rotor_imbalance_and_transient_structural_response"] if scenario.requires_dynamic_balance_model else []
        phase_results: list[FaultPhaseResult] = []
        for phase in mission.phases:
            operating = OperatingPoint(
                phase.operating_point.freestream_velocity,
                phase.operating_point.rpm * scenario.rpm_scale,
                phase.operating_point.collective_pitch_deg + scenario.collective_pitch_delta_deg,
            )
            analysis = analyze_annular_bem(fault_design, medium, operating, registry=registry)
            thrust_margin = analysis.thrust - phase.minimum_thrust
            allowed_power = None if phase.maximum_shaft_power is None else phase.maximum_shaft_power * scenario.available_power_scale
            power_margin = None if allowed_power is None else allowed_power - analysis.shaft_power
            violations: list[str] = []
            if thrust_margin < 0: violations.append("minimum_thrust")
            if power_margin is not None and power_margin < 0: violations.append("available_power")
            if phase.maximum_tip_mach is not None and analysis.tip_mach > phase.maximum_tip_mach: violations.append("maximum_tip_mach")
            if not analysis.converged: violations.append("annular_bem_convergence")
            phase_results.append(FaultPhaseResult(
                phase.name, analysis.thrust, analysis.shaft_power, analysis.tip_mach,
                thrust_margin, power_margin, not violations, tuple(violations)
            ))
        mission_feasible = all(item.feasible for item in phase_results)
        cases.append(FaultCaseResult(
            scenario, blade_count, mission_feasible,
            mission_feasible and not scenario.requires_dynamic_balance_model,
            min(item.thrust_margin for item in phase_results),
            None if all(item.power_margin is None for item in phase_results) else min(item.power_margin for item in phase_results if item.power_margin is not None),
            max(item.tip_mach for item in phase_results), tuple(phase_results), tuple(limitations)
        ))
    critical = min(cases, key=lambda item: item.minimum_thrust_margin)
    return FaultEnvelopeReport(
        mission.name, design.name, len(cases),
        sum(item.mission_feasible for item in cases) / len(cases),
        sum(item.safe_continuation_candidate for item in cases) / len(cases),
        critical.scenario.name, tuple(cases)
    )
