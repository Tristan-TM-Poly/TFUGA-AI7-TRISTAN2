from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from itertools import product
from typing import Any, Iterable

from .analysis import RotorAnalysis, analyze_rotor
from .cavitation import CavitationAssessment, assess_cavitation
from .models import BladeStation, FluidMedium, OperatingPoint, RotorDesign


@dataclass(frozen=True)
class OptimizationConstraints:
    minimum_thrust: float = 0.0
    maximum_shaft_power: float | None = None
    maximum_tip_mach: float = 0.85
    require_positive_cavitation_margin: bool = True

    def validate(self) -> None:
        if self.minimum_thrust < 0 or self.maximum_tip_mach <= 0:
            raise ValueError("invalid optimization constraints")
        if self.maximum_shaft_power is not None and self.maximum_shaft_power <= 0:
            raise ValueError("maximum_shaft_power must be positive")


@dataclass(frozen=True)
class CandidateResult:
    diameter_scale: float
    chord_scale: float
    pitch_delta_deg: float
    analysis: RotorAnalysis
    cavitation: CavitationAssessment
    feasible: bool
    violations: tuple[str, ...]
    noise_proxy: float
    ranking_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "diameter_scale": self.diameter_scale,
            "chord_scale": self.chord_scale,
            "pitch_delta_deg": self.pitch_delta_deg,
            "analysis": self.analysis.to_dict(),
            "cavitation": self.cavitation.to_dict(),
            "feasible": self.feasible,
            "violations": list(self.violations),
            "noise_proxy": self.noise_proxy,
            "ranking_score": self.ranking_score,
        }


@dataclass(frozen=True)
class OptimizationReport:
    candidate_count: int
    feasible_count: int
    best: CandidateResult | None
    pareto_front: tuple[CandidateResult, ...]
    candidates: tuple[CandidateResult, ...]
    ranking_notice: str = "dimensionless min-max screening heuristic; not a certification metric"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_count": self.candidate_count,
            "feasible_count": self.feasible_count,
            "best": None if self.best is None else self.best.to_dict(),
            "pareto_front": [item.to_dict() for item in self.pareto_front],
            "candidates": [item.to_dict() for item in self.candidates],
            "ranking_notice": self.ranking_notice,
        }


def scale_rotor(
    base: RotorDesign,
    *,
    diameter_scale: float,
    chord_scale: float,
    pitch_delta_deg: float,
) -> RotorDesign:
    if diameter_scale <= 0 or chord_scale <= 0:
        raise ValueError("geometry scales must be positive")
    stations = tuple(
        BladeStation(
            radius=station.radius * diameter_scale,
            chord=station.chord * chord_scale,
            twist_deg=station.twist_deg + pitch_delta_deg,
            airfoil_id=station.airfoil_id,
        )
        for station in base.stations
    )
    return RotorDesign(
        name=f"{base.name}-D{diameter_scale:.3f}-C{chord_scale:.3f}-P{pitch_delta_deg:+.2f}",
        blade_count=base.blade_count,
        hub_radius=base.hub_radius * diameter_scale,
        tip_radius=base.tip_radius * diameter_scale,
        stations=stations,
    )


def _violations(
    analysis: RotorAnalysis,
    cavitation: CavitationAssessment,
    constraints: OptimizationConstraints,
) -> tuple[str, ...]:
    failures: list[str] = []
    if analysis.thrust < constraints.minimum_thrust:
        failures.append("minimum_thrust")
    if constraints.maximum_shaft_power is not None and analysis.shaft_power > constraints.maximum_shaft_power:
        failures.append("maximum_shaft_power")
    if analysis.tip_mach > constraints.maximum_tip_mach:
        failures.append("maximum_tip_mach")
    if constraints.require_positive_cavitation_margin and cavitation.applicable and cavitation.risk:
        failures.append("cavitation_margin")
    if not analysis.converged:
        failures.append("induction_convergence")
    return tuple(failures)


def _dominates(left: CandidateResult, right: CandidateResult) -> bool:
    better_or_equal = (
        left.analysis.thrust >= right.analysis.thrust
        and left.analysis.propulsive_efficiency >= right.analysis.propulsive_efficiency
        and left.analysis.shaft_power <= right.analysis.shaft_power
        and left.noise_proxy <= right.noise_proxy
    )
    strictly_better = (
        left.analysis.thrust > right.analysis.thrust
        or left.analysis.propulsive_efficiency > right.analysis.propulsive_efficiency
        or left.analysis.shaft_power < right.analysis.shaft_power
        or left.noise_proxy < right.noise_proxy
    )
    return better_or_equal and strictly_better


def _normalized(values: list[float], value: float) -> float:
    low, high = min(values), max(values)
    return 0.5 if high == low else (value - low) / (high - low)


def grid_optimize(
    base: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    *,
    diameter_scales: Iterable[float],
    chord_scales: Iterable[float],
    pitch_deltas_deg: Iterable[float],
    constraints: OptimizationConstraints | None = None,
) -> OptimizationReport:
    cfg = constraints or OptimizationConstraints()
    cfg.validate()
    raw: list[CandidateResult] = []
    for diameter_scale, chord_scale, pitch_delta in product(
        tuple(diameter_scales), tuple(chord_scales), tuple(pitch_deltas_deg)
    ):
        design = scale_rotor(
            base,
            diameter_scale=diameter_scale,
            chord_scale=chord_scale,
            pitch_delta_deg=pitch_delta,
        )
        analysis = analyze_rotor(design, medium, operating)
        cavitation = assess_cavitation(analysis, medium)
        violations = _violations(analysis, cavitation, cfg)
        noise_proxy = design.blade_count * analysis.tip_mach**5
        raw.append(
            CandidateResult(
                diameter_scale,
                chord_scale,
                pitch_delta,
                analysis,
                cavitation,
                not violations,
                violations,
                noise_proxy,
            )
        )

    feasible = [item for item in raw if item.feasible]
    scored = raw
    if feasible:
        thrusts = [item.analysis.thrust for item in feasible]
        efficiencies = [item.analysis.propulsive_efficiency for item in feasible]
        powers = [item.analysis.shaft_power for item in feasible]
        noises = [item.noise_proxy for item in feasible]
        score_by_name: dict[str, float] = {}
        for item in feasible:
            score_by_name[item.analysis.design_name] = (
                0.35 * _normalized(thrusts, item.analysis.thrust)
                + 0.35 * _normalized(efficiencies, item.analysis.propulsive_efficiency)
                - 0.20 * _normalized(powers, item.analysis.shaft_power)
                - 0.10 * _normalized(noises, item.noise_proxy)
            )
        scored = [
            replace(item, ranking_score=score_by_name.get(item.analysis.design_name, -1.0)) for item in raw
        ]
        feasible = [item for item in scored if item.feasible]

    pareto = tuple(
        candidate
        for candidate in feasible
        if not any(_dominates(other, candidate) for other in feasible if other is not candidate)
    )
    best = max(feasible, key=lambda item: item.ranking_score) if feasible else None
    return OptimizationReport(len(scored), len(feasible), best, pareto, tuple(scored))
