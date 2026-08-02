from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Iterable, Iterator

from .acoustics import AcousticLimits, AcousticScreenReport, screen_rotor_acoustics
from .annular_bem import analyze_annular_bem
from .faults import FaultEnvelopeReport, FaultScenario, evaluate_fault_envelope
from .materials import MaterialAtlas, default_material_atlas
from .mission import MissionGenome, MissionPhase
from .models import FluidMedium, OperatingPoint, RotorDesign
from .optimizer import scale_rotor
from .polars import PolarRegistry
from .robust_mission import MissionUncertaintyCase, RobustMissionReport, evaluate_robust_mission
from .structural import StructuralAssumptions, StructuralBladeReport, analyze_blade_structure


def _radical_inverse(index: int, base: int) -> float:
    if index < 0 or base < 2:
        raise ValueError("index must be non-negative and base at least two")
    value = 0.0
    denominator = 1.0
    current = index
    while current:
        current, remainder = divmod(current, base)
        denominator *= base
        value += remainder / denominator
    return value


def _lerp(low: float, high: float, fraction: float) -> float:
    return low + (high - low) * fraction


@dataclass(frozen=True)
class SystemDesignVector:
    frontier_index: int
    candidate_id: str
    diameter_scale: float
    chord_scale: float
    pitch_delta_deg: float
    rpm_scale: float
    material_name: str

    def validate(self) -> None:
        if self.frontier_index < 0 or not self.candidate_id.strip() or not self.material_name.strip():
            raise ValueError("invalid frontier identity")
        if self.diameter_scale <= 0 or self.chord_scale <= 0 or self.rpm_scale <= 0:
            raise ValueError("geometry and RPM scales must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "frontier_index": self.frontier_index,
            "candidate_id": self.candidate_id,
            "diameter_scale": self.diameter_scale,
            "chord_scale": self.chord_scale,
            "pitch_delta_deg": self.pitch_delta_deg,
            "rpm_scale": self.rpm_scale,
            "material_name": self.material_name,
        }


@dataclass(frozen=True)
class InfiniteSystemFrontier:
    diameter_scale_bounds: tuple[float, float] = (0.82, 1.22)
    chord_scale_bounds: tuple[float, float] = (0.75, 1.25)
    pitch_delta_bounds_deg: tuple[float, float] = (-6.0, 6.0)
    rpm_scale_bounds: tuple[float, float] = (0.78, 1.12)
    namespace: str = "omega-propulsion-r03-max"

    def validate(self) -> None:
        for name, bounds in (
            ("diameter", self.diameter_scale_bounds),
            ("chord", self.chord_scale_bounds),
            ("pitch", self.pitch_delta_bounds_deg),
            ("rpm", self.rpm_scale_bounds),
        ):
            if len(bounds) != 2 or bounds[0] >= bounds[1]:
                raise ValueError(f"invalid {name} bounds")
        if self.diameter_scale_bounds[0] <= 0 or self.chord_scale_bounds[0] <= 0 or self.rpm_scale_bounds[0] <= 0:
            raise ValueError("positive scale lower bounds are required")
        if not self.namespace.strip():
            raise ValueError("frontier namespace cannot be empty")

    def vector_at(self, index: int, atlas: MaterialAtlas | None = None) -> SystemDesignVector:
        self.validate()
        if index < 0:
            raise ValueError("frontier index must be non-negative")
        material_atlas = atlas or default_material_atlas()
        if not material_atlas.names:
            raise ValueError("material atlas cannot be empty")
        sequence_index = index + 1
        vector = SystemDesignVector(
            frontier_index=index,
            candidate_id=f"{self.namespace}:{index:016d}",
            diameter_scale=_lerp(*self.diameter_scale_bounds, _radical_inverse(sequence_index, 2)),
            chord_scale=_lerp(*self.chord_scale_bounds, _radical_inverse(sequence_index, 3)),
            pitch_delta_deg=_lerp(*self.pitch_delta_bounds_deg, _radical_inverse(sequence_index, 5)),
            rpm_scale=_lerp(*self.rpm_scale_bounds, _radical_inverse(sequence_index, 7)),
            material_name=material_atlas.names[index % len(material_atlas.names)],
        )
        vector.validate()
        return vector

    def stream(self, start_index: int = 0, atlas: MaterialAtlas | None = None) -> Iterator[SystemDesignVector]:
        if start_index < 0:
            raise ValueError("start_index must be non-negative")
        index = start_index
        while True:
            yield self.vector_at(index, atlas)
            index += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "diameter_scale_bounds": list(self.diameter_scale_bounds),
            "chord_scale_bounds": list(self.chord_scale_bounds),
            "pitch_delta_bounds_deg": list(self.pitch_delta_bounds_deg),
            "rpm_scale_bounds": list(self.rpm_scale_bounds),
            "namespace": self.namespace,
            "permanent_total_cap": None,
            "execution_rule": "unbounded deterministic stream; every run remains finite and resource-bounded",
        }


@dataclass(frozen=True)
class SystemSearchConstraints:
    maximum_rotor_mass_kg: float | None = 15.0
    minimum_structural_safety_factor: float = 1.5
    maximum_overall_spl_db: float | None = 105.0
    minimum_robust_feasible_probability: float = 0.75
    minimum_safe_continuation_fraction: float = 0.25
    maximum_expected_shaft_energy_j: float | None = None
    maximum_tip_mach: float = 0.85

    def validate(self) -> None:
        if self.maximum_rotor_mass_kg is not None and self.maximum_rotor_mass_kg <= 0:
            raise ValueError("maximum_rotor_mass_kg must be positive")
        if self.minimum_structural_safety_factor <= 0 or self.maximum_tip_mach <= 0:
            raise ValueError("safety factor and tip Mach limits must be positive")
        for name, value in (
            ("minimum_robust_feasible_probability", self.minimum_robust_feasible_probability),
            ("minimum_safe_continuation_fraction", self.minimum_safe_continuation_fraction),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.maximum_overall_spl_db is not None and self.maximum_overall_spl_db <= 0:
            raise ValueError("maximum_overall_spl_db must be positive")
        if self.maximum_expected_shaft_energy_j is not None and self.maximum_expected_shaft_energy_j <= 0:
            raise ValueError("maximum_expected_shaft_energy_j must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "maximum_rotor_mass_kg": self.maximum_rotor_mass_kg,
            "minimum_structural_safety_factor": self.minimum_structural_safety_factor,
            "maximum_overall_spl_db": self.maximum_overall_spl_db,
            "minimum_robust_feasible_probability": self.minimum_robust_feasible_probability,
            "minimum_safe_continuation_fraction": self.minimum_safe_continuation_fraction,
            "maximum_expected_shaft_energy_j": self.maximum_expected_shaft_energy_j,
            "maximum_tip_mach": self.maximum_tip_mach,
        }


@dataclass(frozen=True)
class SystemObjectives:
    expected_shaft_energy_j: float
    rotor_mass_kg: float
    acoustic_spl_db: float
    worst_mission_efficiency: float
    minimum_safety_factor: float
    robust_feasible_probability: float
    safe_continuation_fraction: float

    def to_dict(self) -> dict[str, float]:
        return {
            "expected_shaft_energy_j": self.expected_shaft_energy_j,
            "rotor_mass_kg": self.rotor_mass_kg,
            "acoustic_spl_db": self.acoustic_spl_db,
            "worst_mission_efficiency": self.worst_mission_efficiency,
            "minimum_safety_factor": self.minimum_safety_factor,
            "robust_feasible_probability": self.robust_feasible_probability,
            "safe_continuation_fraction": self.safe_continuation_fraction,
        }


@dataclass(frozen=True)
class SystemCandidateResult:
    vector: SystemDesignVector
    design_name: str
    critical_structural_phase: str
    critical_acoustic_phase: str
    structural: StructuralBladeReport
    acoustic: AcousticScreenReport
    robust_mission: RobustMissionReport
    fault_envelope: FaultEnvelopeReport
    objectives: SystemObjectives
    feasible: bool
    violations: tuple[str, ...]
    evidence_hash: str
    ranking_score: float = 0.0
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector": self.vector.to_dict(),
            "design_name": self.design_name,
            "critical_structural_phase": self.critical_structural_phase,
            "critical_acoustic_phase": self.critical_acoustic_phase,
            "structural": self.structural.to_dict(),
            "acoustic": self.acoustic.to_dict(),
            "robust_mission": self.robust_mission.to_dict(),
            "fault_envelope": self.fault_envelope.to_dict(),
            "objectives": self.objectives.to_dict(),
            "feasible": self.feasible,
            "violations": list(self.violations),
            "evidence_hash": self.evidence_hash,
            "ranking_score": self.ranking_score,
            "physics_certified": self.physics_certified,
        }


@dataclass(frozen=True)
class CampaignCheckpoint:
    next_index: int
    run_evaluated_count: int
    run_feasible_count: int
    chain_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "next_index": self.next_index,
            "run_evaluated_count": self.run_evaluated_count,
            "run_feasible_count": self.run_feasible_count,
            "chain_digest": self.chain_digest,
        }


@dataclass(frozen=True)
class SystemCampaignReport:
    start_index: int
    requested_count: int
    evaluated_count: int
    feasible_count: int
    next_index: int
    best: SystemCandidateResult | None
    pareto_front: tuple[SystemCandidateResult, ...]
    candidates: tuple[SystemCandidateResult, ...]
    checkpoints: tuple[CampaignCheckpoint, ...]
    final_chain_digest: str
    frontier: InfiniteSystemFrontier
    constraints: SystemSearchConstraints
    permanent_total_cap: None = None
    physics_certified: bool = False
    certification_notice: str = "research screening and search evidence only; not design approval, airworthiness or seaworthiness certification"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_index": self.start_index,
            "requested_count": self.requested_count,
            "evaluated_count": self.evaluated_count,
            "feasible_count": self.feasible_count,
            "next_index": self.next_index,
            "best": None if self.best is None else self.best.to_dict(),
            "pareto_front": [item.to_dict() for item in self.pareto_front],
            "candidates": [item.to_dict() for item in self.candidates],
            "checkpoints": [item.to_dict() for item in self.checkpoints],
            "final_chain_digest": self.final_chain_digest,
            "frontier": self.frontier.to_dict(),
            "constraints": self.constraints.to_dict(),
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def _scaled_mission(mission: MissionGenome, rpm_scale: float) -> MissionGenome:
    phases = tuple(
        MissionPhase(
            phase.name,
            phase.duration_s,
            OperatingPoint(
                phase.operating_point.freestream_velocity,
                phase.operating_point.rpm * rpm_scale,
                phase.operating_point.collective_pitch_deg,
            ),
            phase.minimum_thrust,
            phase.maximum_shaft_power,
            phase.maximum_tip_mach,
            phase.importance_weight,
        )
        for phase in mission.phases
    )
    return MissionGenome.from_phases(
        name=f"{mission.name}:rpm-scale-{rpm_scale:.8f}",
        domain=mission.domain,
        vehicle=mission.vehicle,
        phases=phases,
        objectives=mission.objectives,
        provenance=f"{mission.provenance}; system frontier RPM scale={rpm_scale:.8f}",
    )


def _candidate_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_system_candidate(
    base_design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    vector: SystemDesignVector,
    *,
    atlas: MaterialAtlas | None = None,
    constraints: SystemSearchConstraints | None = None,
    registry: PolarRegistry | None = None,
    uncertainty_cases: Iterable[MissionUncertaintyCase] | None = None,
    fault_scenarios: Iterable[FaultScenario] | None = None,
    observer_distance_m: float = 10.0,
) -> SystemCandidateResult:
    base_design.validate()
    medium.validate()
    mission.validate()
    vector.validate()
    cfg = constraints or SystemSearchConstraints()
    cfg.validate()
    material_atlas = atlas or default_material_atlas()
    material = material_atlas.get(vector.material_name)
    design = scale_rotor(
        base_design,
        diameter_scale=vector.diameter_scale,
        chord_scale=vector.chord_scale,
        pitch_delta_deg=vector.pitch_delta_deg,
    )
    scaled_mission = _scaled_mission(mission, vector.rpm_scale)

    structural_by_phase: list[tuple[str, StructuralBladeReport]] = []
    acoustic_by_phase: list[tuple[str, AcousticScreenReport]] = []
    for phase in scaled_mission.phases:
        aerodynamic = analyze_annular_bem(design, medium, phase.operating_point, registry=registry)
        structural_by_phase.append(
            (
                phase.name,
                analyze_blade_structure(
                    design,
                    phase.operating_point,
                    aerodynamic,
                    material=material,
                    assumptions=StructuralAssumptions(
                        minimum_safety_factor=cfg.minimum_structural_safety_factor
                    ),
                ),
            )
        )
        acoustic_by_phase.append(
            (
                phase.name,
                screen_rotor_acoustics(
                    design,
                    phase.operating_point,
                    aerodynamic,
                    observer_distance_m=observer_distance_m,
                    limits=AcousticLimits(
                        maximum_overall_spl_db=cfg.maximum_overall_spl_db,
                        maximum_tip_mach=cfg.maximum_tip_mach,
                    ),
                ),
            )
        )

    critical_structural_phase, structural = min(
        structural_by_phase, key=lambda item: item[1].minimum_safety_factor
    )
    critical_acoustic_phase, acoustic = max(
        acoustic_by_phase, key=lambda item: item[1].estimated_overall_spl_db
    )
    robust = evaluate_robust_mission(
        design,
        medium,
        scaled_mission,
        cases=uncertainty_cases,
        registry=registry,
    )
    faults = evaluate_fault_envelope(
        design,
        medium,
        scaled_mission,
        scenarios=fault_scenarios,
        registry=registry,
    )
    objectives = SystemObjectives(
        expected_shaft_energy_j=robust.expected_shaft_energy_j,
        rotor_mass_kg=structural.rotor_mass,
        acoustic_spl_db=acoustic.estimated_overall_spl_db,
        worst_mission_efficiency=robust.worst_mission_efficiency,
        minimum_safety_factor=structural.minimum_safety_factor,
        robust_feasible_probability=robust.feasible_probability,
        safe_continuation_fraction=faults.safe_continuation_fraction,
    )
    violations: list[str] = []
    if not structural.feasible:
        violations.extend(f"structural:{item}" for item in structural.violations)
    if not acoustic.feasible:
        violations.extend(f"acoustic:{item}" for item in acoustic.violations)
    if cfg.maximum_rotor_mass_kg is not None and structural.rotor_mass > cfg.maximum_rotor_mass_kg:
        violations.append("system:maximum_rotor_mass_kg")
    if structural.minimum_safety_factor < cfg.minimum_structural_safety_factor:
        violations.append("system:minimum_structural_safety_factor")
    if robust.feasible_probability < cfg.minimum_robust_feasible_probability:
        violations.append("system:minimum_robust_feasible_probability")
    if faults.safe_continuation_fraction < cfg.minimum_safe_continuation_fraction:
        violations.append("system:minimum_safe_continuation_fraction")
    if cfg.maximum_expected_shaft_energy_j is not None and robust.expected_shaft_energy_j > cfg.maximum_expected_shaft_energy_j:
        violations.append("system:maximum_expected_shaft_energy_j")
    if robust.maximum_tip_mach > cfg.maximum_tip_mach:
        violations.append("system:maximum_tip_mach")
    stable_payload = {
        "vector": vector.to_dict(),
        "design_name": design.name,
        "critical_structural_phase": critical_structural_phase,
        "critical_acoustic_phase": critical_acoustic_phase,
        "objectives": objectives.to_dict(),
        "violations": violations,
        "models": {
            "structural": structural.model,
            "acoustic": acoustic.model,
            "robust": robust.model,
            "faults": faults.model,
        },
    }
    return SystemCandidateResult(
        vector=vector,
        design_name=design.name,
        critical_structural_phase=critical_structural_phase,
        critical_acoustic_phase=critical_acoustic_phase,
        structural=structural,
        acoustic=acoustic,
        robust_mission=robust,
        fault_envelope=faults,
        objectives=objectives,
        feasible=not violations,
        violations=tuple(violations),
        evidence_hash=_candidate_digest(stable_payload),
    )


def _dominates(left: SystemCandidateResult, right: SystemCandidateResult) -> bool:
    a = left.objectives
    b = right.objectives
    better_or_equal = (
        a.expected_shaft_energy_j <= b.expected_shaft_energy_j
        and a.rotor_mass_kg <= b.rotor_mass_kg
        and a.acoustic_spl_db <= b.acoustic_spl_db
        and a.worst_mission_efficiency >= b.worst_mission_efficiency
        and a.minimum_safety_factor >= b.minimum_safety_factor
        and a.robust_feasible_probability >= b.robust_feasible_probability
        and a.safe_continuation_fraction >= b.safe_continuation_fraction
    )
    strictly_better = (
        a.expected_shaft_energy_j < b.expected_shaft_energy_j
        or a.rotor_mass_kg < b.rotor_mass_kg
        or a.acoustic_spl_db < b.acoustic_spl_db
        or a.worst_mission_efficiency > b.worst_mission_efficiency
        or a.minimum_safety_factor > b.minimum_safety_factor
        or a.robust_feasible_probability > b.robust_feasible_probability
        or a.safe_continuation_fraction > b.safe_continuation_fraction
    )
    return better_or_equal and strictly_better


def _normalized(values: list[float], value: float) -> float:
    low = min(values)
    high = max(values)
    return 0.5 if high == low else (value - low) / (high - low)


def _score_candidates(candidates: list[SystemCandidateResult]) -> list[SystemCandidateResult]:
    feasible = [item for item in candidates if item.feasible]
    if not feasible:
        return candidates
    energies = [item.objectives.expected_shaft_energy_j for item in feasible]
    masses = [item.objectives.rotor_mass_kg for item in feasible]
    acoustics = [item.objectives.acoustic_spl_db for item in feasible]
    efficiencies = [item.objectives.worst_mission_efficiency for item in feasible]
    safeties = [item.objectives.minimum_safety_factor for item in feasible]
    probabilities = [item.objectives.robust_feasible_probability for item in feasible]
    continuations = [item.objectives.safe_continuation_fraction for item in feasible]
    scores: dict[str, float] = {}
    for item in feasible:
        obj = item.objectives
        scores[item.vector.candidate_id] = (
            0.22 * _normalized(efficiencies, obj.worst_mission_efficiency)
            + 0.18 * _normalized(safeties, obj.minimum_safety_factor)
            + 0.15 * _normalized(probabilities, obj.robust_feasible_probability)
            + 0.15 * _normalized(continuations, obj.safe_continuation_fraction)
            - 0.15 * _normalized(energies, obj.expected_shaft_energy_j)
            - 0.10 * _normalized(masses, obj.rotor_mass_kg)
            - 0.05 * _normalized(acoustics, obj.acoustic_spl_db)
        )
    return [
        replace(item, ranking_score=scores.get(item.vector.candidate_id, -1.0))
        for item in candidates
    ]


def run_system_campaign(
    base_design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    *,
    start_index: int,
    count: int,
    frontier: InfiniteSystemFrontier | None = None,
    atlas: MaterialAtlas | None = None,
    constraints: SystemSearchConstraints | None = None,
    registry: PolarRegistry | None = None,
    uncertainty_cases: Iterable[MissionUncertaintyCase] | None = None,
    fault_scenarios: Iterable[FaultScenario] | None = None,
    observer_distance_m: float = 10.0,
    checkpoint_interval: int = 8,
    previous_chain_digest: str = "0" * 64,
) -> SystemCampaignReport:
    if start_index < 0 or count < 1 or checkpoint_interval < 1:
        raise ValueError("start_index must be non-negative and count/checkpoint_interval positive")
    if len(previous_chain_digest) != 64:
        raise ValueError("previous_chain_digest must be a 64-character SHA-256 hex digest")
    try:
        bytes.fromhex(previous_chain_digest)
    except ValueError as exc:
        raise ValueError("previous_chain_digest must be hexadecimal") from exc
    search_frontier = frontier or InfiniteSystemFrontier()
    material_atlas = atlas or default_material_atlas()
    cfg = constraints or SystemSearchConstraints()
    search_frontier.validate()
    cfg.validate()

    raw: list[SystemCandidateResult] = []
    checkpoints: list[CampaignCheckpoint] = []
    chain_digest = previous_chain_digest
    feasible_count = 0
    for offset in range(count):
        index = start_index + offset
        vector = search_frontier.vector_at(index, material_atlas)
        candidate = evaluate_system_candidate(
            base_design,
            medium,
            mission,
            vector,
            atlas=material_atlas,
            constraints=cfg,
            registry=registry,
            uncertainty_cases=uncertainty_cases,
            fault_scenarios=fault_scenarios,
            observer_distance_m=observer_distance_m,
        )
        raw.append(candidate)
        feasible_count += int(candidate.feasible)
        chain_digest = hashlib.sha256(
            f"{chain_digest}:{candidate.evidence_hash}".encode("ascii")
        ).hexdigest()
        evaluated = offset + 1
        if evaluated % checkpoint_interval == 0 or evaluated == count:
            checkpoints.append(
                CampaignCheckpoint(
                    next_index=index + 1,
                    run_evaluated_count=evaluated,
                    run_feasible_count=feasible_count,
                    chain_digest=chain_digest,
                )
            )

    scored = _score_candidates(raw)
    feasible = [item for item in scored if item.feasible]
    pareto = tuple(
        candidate
        for candidate in feasible
        if not any(_dominates(other, candidate) for other in feasible if other is not candidate)
    )
    best = max(feasible, key=lambda item: item.ranking_score) if feasible else None
    return SystemCampaignReport(
        start_index=start_index,
        requested_count=count,
        evaluated_count=len(scored),
        feasible_count=len(feasible),
        next_index=start_index + count,
        best=best,
        pareto_front=pareto,
        candidates=tuple(scored),
        checkpoints=tuple(checkpoints),
        final_chain_digest=chain_digest,
        frontier=search_frontier,
        constraints=cfg,
    )
