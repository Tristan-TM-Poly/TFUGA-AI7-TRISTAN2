from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from math import ceil, pi, sqrt
from typing import Any, Iterable, Sequence

from .faults import FaultScenario, default_fault_scenarios
from .materials import MaterialAtlas, default_material_atlas
from .mission import MissionGenome
from .models import FluidMedium, RotorDesign
from .optimizer import scale_rotor
from .polars import PolarRegistry
from .robust_mission import MissionUncertaintyCase, default_uncertainty_cases
from .system_optimizer import (
    InfiniteSystemFrontier,
    SystemCandidateResult,
    SystemDesignVector,
    SystemSearchConstraints,
    evaluate_system_candidate,
)


STAGE_ORDER = {"F0_ANALYTIC": 0, "F1_SYSTEM": 1, "F2_STRESS": 2}


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FidelityDefinition:
    name: str
    cost_units: float
    description: str
    physical_fidelity_claim: bool = False

    def validate(self) -> None:
        if self.name not in STAGE_ORDER:
            raise ValueError(f"unknown fidelity stage: {self.name}")
        if self.cost_units <= 0 or not self.description.strip():
            raise ValueError("fidelity stage requires positive cost and description")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MultiFidelityPolicy:
    f0: FidelityDefinition = FidelityDefinition(
        "F0_ANALYTIC",
        1.0,
        "geometry, mass, solidity, disk-loading and tip-Mach screening",
    )
    f1: FidelityDefinition = FidelityDefinition(
        "F1_SYSTEM",
        24.0,
        "R0.3 Max structural, acoustic, robust-mission and fault evidence",
    )
    f2: FidelityDefinition = FidelityDefinition(
        "F2_STRESS",
        72.0,
        "expanded deterministic uncertainty and fault stress scenarios using the same low-order physics",
    )
    f1_utility_threshold: float = 0.18
    f2_score_threshold: float = -0.15
    f0_tip_mach_margin: float = 1.12
    f0_mass_margin: float = 1.30
    preserve_candidate_local_decisions: bool = True

    def validate(self) -> None:
        self.f0.validate()
        self.f1.validate()
        self.f2.validate()
        if not -1.0 <= self.f1_utility_threshold <= 1.0:
            raise ValueError("f1_utility_threshold must lie in [-1, 1]")
        if not -2.0 <= self.f2_score_threshold <= 2.0:
            raise ValueError("f2_score_threshold must lie in [-2, 2]")
        if self.f0_tip_mach_margin < 1.0 or self.f0_mass_margin < 1.0:
            raise ValueError("F0 margins must be at least one")

    def to_dict(self) -> dict[str, Any]:
        return {
            "f0": self.f0.to_dict(),
            "f1": self.f1.to_dict(),
            "f2": self.f2.to_dict(),
            "f1_utility_threshold": self.f1_utility_threshold,
            "f2_score_threshold": self.f2_score_threshold,
            "f0_tip_mach_margin": self.f0_tip_mach_margin,
            "f0_mass_margin": self.f0_mass_margin,
            "preserve_candidate_local_decisions": self.preserve_candidate_local_decisions,
            "permanent_total_cap": None,
        }


@dataclass(frozen=True)
class ResourceEnvelope:
    max_cost_units: float
    checkpoint_interval: int = 8
    shard_count: int = 1

    def validate(self) -> None:
        if self.max_cost_units <= 0:
            raise ValueError("max_cost_units must be positive")
        if self.checkpoint_interval < 1 or self.shard_count < 1:
            raise ValueError("checkpoint_interval and shard_count must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_cost_units": self.max_cost_units,
            "checkpoint_interval": self.checkpoint_interval,
            "shard_count": self.shard_count,
            "scope": "finite execution envelope; not a permanent frontier cap",
        }


@dataclass(frozen=True)
class F0ScreenResult:
    vector: SystemDesignVector
    estimated_tip_mach: float
    estimated_rotor_mass_kg: float
    disk_loading_proxy_pa: float
    mean_solidity_proxy: float
    utility: float
    passed: bool
    rejection_reasons: tuple[str, ...]
    evidence_hash: str
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector": self.vector.to_dict(),
            "estimated_tip_mach": self.estimated_tip_mach,
            "estimated_rotor_mass_kg": self.estimated_rotor_mass_kg,
            "disk_loading_proxy_pa": self.disk_loading_proxy_pa,
            "mean_solidity_proxy": self.mean_solidity_proxy,
            "utility": self.utility,
            "passed": self.passed,
            "rejection_reasons": list(self.rejection_reasons),
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
        }


@dataclass(frozen=True)
class PromotionDecision:
    candidate_id: str
    frontier_index: int
    from_stage: str
    to_stage: str
    promoted: bool
    metric: float
    threshold: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceEvent:
    frontier_index: int
    candidate_id: str
    stage: str
    evidence_hash: str

    def validate(self) -> None:
        if self.frontier_index < 0 or self.stage not in STAGE_ORDER:
            raise ValueError("invalid evidence event")
        if len(self.evidence_hash) != 64:
            raise ValueError("evidence_hash must be SHA-256 length")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MultiFidelityCandidate:
    f0: F0ScreenResult
    f1: SystemCandidateResult | None
    f2: SystemCandidateResult | None
    final_stage: str
    final_score: float
    promoted_to_f1: bool
    promoted_to_f2: bool
    resource_limited: bool

    @property
    def final_result(self) -> SystemCandidateResult | None:
        return self.f2 or self.f1

    @property
    def feasible(self) -> bool:
        result = self.final_result
        return bool(result and result.feasible)

    def to_dict(self) -> dict[str, Any]:
        return {
            "f0": self.f0.to_dict(),
            "f1": None if self.f1 is None else self.f1.to_dict(),
            "f2": None if self.f2 is None else self.f2.to_dict(),
            "final_stage": self.final_stage,
            "final_score": self.final_score,
            "promoted_to_f1": self.promoted_to_f1,
            "promoted_to_f2": self.promoted_to_f2,
            "resource_limited": self.resource_limited,
            "feasible": self.feasible,
        }


@dataclass(frozen=True)
class MMinusRecord:
    signature: str
    stage: str
    reason: str
    count: int
    first_frontier_index: int
    last_frontier_index: int
    sample_candidate_ids: tuple[str, ...]
    action: str = "retain as negative evidence; do not convert into an automatic permanent exclusion"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signature": self.signature,
            "stage": self.stage,
            "reason": self.reason,
            "count": self.count,
            "first_frontier_index": self.first_frontier_index,
            "last_frontier_index": self.last_frontier_index,
            "sample_candidate_ids": list(self.sample_candidate_ids),
            "action": self.action,
        }


@dataclass(frozen=True)
class MultiFidelityCheckpoint:
    next_index: int
    evidence_event_count: int
    consumed_cost_units: float
    chain_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackpressureState:
    requested_count: int
    admitted_f0_count: int
    f1_count: int
    f2_count: int
    consumed_cost_units: float
    remaining_cost_units: float
    pressure_ratio: float
    next_recommended_count: int
    stop_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShardManifest:
    campaign_id: str
    shard_id: int
    start_index: int
    count: int
    seed_digest: str

    @property
    def end_index_exclusive(self) -> int:
        return self.start_index + self.count

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "shard_id": self.shard_id,
            "start_index": self.start_index,
            "count": self.count,
            "end_index_exclusive": self.end_index_exclusive,
            "seed_digest": self.seed_digest,
        }


@dataclass(frozen=True)
class MultiFidelityCampaignReport:
    campaign_id: str
    start_index: int
    requested_count: int
    next_index: int
    candidates: tuple[MultiFidelityCandidate, ...]
    promotions: tuple[PromotionDecision, ...]
    evidence_events: tuple[EvidenceEvent, ...]
    pareto_front: tuple[SystemCandidateResult, ...]
    best: SystemCandidateResult | None
    m_minus: tuple[MMinusRecord, ...]
    checkpoints: tuple[MultiFidelityCheckpoint, ...]
    consumed_cost_units: float
    final_chain_digest: str
    backpressure: BackpressureState
    policy: MultiFidelityPolicy
    resources: ResourceEnvelope
    frontier: InfiniteSystemFrontier
    permanent_total_cap: None = None
    physics_certified: bool = False
    certification_notice: str = (
        "adaptive evidence-depth search only; F2 is expanded low-order stress testing, "
        "not CFD, FSI, experiment, design approval, airworthiness or seaworthiness certification"
    )

    @property
    def f0_count(self) -> int:
        return len(self.candidates)

    @property
    def f1_count(self) -> int:
        return sum(item.f1 is not None for item in self.candidates)

    @property
    def f2_count(self) -> int:
        return sum(item.f2 is not None for item in self.candidates)

    @property
    def feasible_count(self) -> int:
        return sum(item.feasible for item in self.candidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "start_index": self.start_index,
            "requested_count": self.requested_count,
            "next_index": self.next_index,
            "f0_count": self.f0_count,
            "f1_count": self.f1_count,
            "f2_count": self.f2_count,
            "feasible_count": self.feasible_count,
            "candidates": [item.to_dict() for item in self.candidates],
            "promotions": [item.to_dict() for item in self.promotions],
            "evidence_events": [item.to_dict() for item in self.evidence_events],
            "pareto_front": [item.to_dict() for item in self.pareto_front],
            "best": None if self.best is None else self.best.to_dict(),
            "m_minus": [item.to_dict() for item in self.m_minus],
            "checkpoints": [item.to_dict() for item in self.checkpoints],
            "consumed_cost_units": self.consumed_cost_units,
            "final_chain_digest": self.final_chain_digest,
            "backpressure": self.backpressure.to_dict(),
            "policy": self.policy.to_dict(),
            "resources": self.resources.to_dict(),
            "frontier": self.frontier.to_dict(),
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


@dataclass(frozen=True)
class MergedShardReport:
    campaign_id: str
    start_index: int
    next_index: int
    shard_count: int
    evaluated_count: int
    evidence_event_count: int
    final_chain_digest: str
    pareto_front: tuple[SystemCandidateResult, ...]
    best: SystemCandidateResult | None
    m_minus: tuple[MMinusRecord, ...]
    permanent_total_cap: None = None
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "start_index": self.start_index,
            "next_index": self.next_index,
            "shard_count": self.shard_count,
            "evaluated_count": self.evaluated_count,
            "evidence_event_count": self.evidence_event_count,
            "final_chain_digest": self.final_chain_digest,
            "pareto_front": [item.to_dict() for item in self.pareto_front],
            "best": None if self.best is None else self.best.to_dict(),
            "m_minus": [item.to_dict() for item in self.m_minus],
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
        }


def _estimate_rotor_mass(design: RotorDesign, density: float) -> float:
    total_per_blade = 0.0
    for left, right in zip(design.stations, design.stations[1:]):
        width = right.radius - left.radius
        chord = 0.5 * (left.chord + right.chord)
        thickness = 0.14 * chord
        effective_area = 0.22 * chord * thickness
        total_per_blade += density * effective_area * width
    return design.blade_count * total_per_blade


def screen_f0(
    base_design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    vector: SystemDesignVector,
    *,
    atlas: MaterialAtlas | None = None,
    constraints: SystemSearchConstraints | None = None,
    policy: MultiFidelityPolicy | None = None,
) -> F0ScreenResult:
    base_design.validate()
    medium.validate()
    mission.validate()
    vector.validate()
    material_atlas = atlas or default_material_atlas()
    cfg = constraints or SystemSearchConstraints()
    pol = policy or MultiFidelityPolicy()
    cfg.validate()
    pol.validate()
    material = material_atlas.get(vector.material_name)
    design = scale_rotor(
        base_design,
        diameter_scale=vector.diameter_scale,
        chord_scale=vector.chord_scale,
        pitch_delta_deg=vector.pitch_delta_deg,
    )
    max_rpm = max(phase.operating_point.rpm for phase in mission.phases) * vector.rpm_scale
    max_velocity = max(abs(phase.operating_point.freestream_velocity) for phase in mission.phases)
    tip_tangential = pi * design.diameter * max_rpm / 60.0
    tip_mach = sqrt(tip_tangential**2 + max_velocity**2) / medium.sound_speed
    rotor_mass = _estimate_rotor_mass(design, material.density)
    minimum_thrust = max(phase.minimum_thrust for phase in mission.phases)
    disk_loading = minimum_thrust / max(design.disk_area, 1e-12)
    mean_chord = sum(station.chord for station in design.stations) / len(design.stations)
    solidity = design.blade_count * mean_chord / max(pi * design.diameter, 1e-12)

    reasons: list[str] = []
    if tip_mach > cfg.maximum_tip_mach * pol.f0_tip_mach_margin:
        reasons.append("f0:tip_mach_proxy")
    if cfg.maximum_rotor_mass_kg is not None and rotor_mass > cfg.maximum_rotor_mass_kg * pol.f0_mass_margin:
        reasons.append("f0:rotor_mass_proxy")
    if not 0.01 <= solidity <= 0.60:
        reasons.append("f0:solidity_proxy")
    if disk_loading <= 0:
        reasons.append("f0:disk_loading_proxy")

    mach_utility = 1.0 - min(2.0, abs(tip_mach - 0.55) / 0.55)
    mass_reference = cfg.maximum_rotor_mass_kg or max(rotor_mass, 1.0)
    mass_utility = 1.0 - min(2.0, rotor_mass / max(mass_reference, 1e-12))
    solidity_utility = 1.0 - min(2.0, abs(solidity - 0.10) / 0.10)
    disk_utility = 1.0 / (1.0 + disk_loading / 2000.0)
    utility = 0.35 * mach_utility + 0.30 * mass_utility + 0.20 * solidity_utility + 0.15 * disk_utility
    stable = {
        "vector": vector.to_dict(),
        "tip_mach": tip_mach,
        "rotor_mass": rotor_mass,
        "disk_loading": disk_loading,
        "solidity": solidity,
        "reasons": reasons,
    }
    return F0ScreenResult(
        vector,
        tip_mach,
        rotor_mass,
        disk_loading,
        solidity,
        utility,
        not reasons,
        tuple(reasons),
        _digest(stable),
    )


def expanded_uncertainty_cases() -> tuple[MissionUncertaintyCase, ...]:
    return default_uncertainty_cases() + (
        MissionUncertaintyCase(
            "severe-hot-headwind-rpm-derate",
            density_scale=0.80,
            viscosity_scale=1.12,
            sound_speed_scale=1.06,
            velocity_scale=1.20,
            rpm_scale=0.88,
            collective_pitch_delta_deg=1.5,
        ),
        MissionUncertaintyCase(
            "severe-cold-control-bias",
            density_scale=1.18,
            viscosity_scale=0.88,
            sound_speed_scale=0.94,
            velocity_scale=0.92,
            rpm_scale=1.06,
            collective_pitch_delta_deg=-2.0,
        ),
    )


def expanded_fault_scenarios() -> tuple[FaultScenario, ...]:
    return default_fault_scenarios() + (
        FaultScenario(
            "rpm-derate-20pct",
            rpm_scale=0.80,
            available_power_scale=0.64,
            severity="major",
        ),
        FaultScenario(
            "pitch-jam-plus-5deg",
            collective_pitch_delta_deg=5.0,
            available_power_scale=0.90,
            severity="major",
        ),
    )


def _candidate_score(result: SystemCandidateResult) -> float:
    obj = result.objectives
    penalty = 0.25 * len(result.violations)
    return (
        0.95 * obj.worst_mission_efficiency
        + 0.40 * obj.robust_feasible_probability
        + 0.30 * obj.safe_continuation_fraction
        + 0.10 * min(obj.minimum_safety_factor, 10.0)
        - 0.20 * (obj.expected_shaft_energy_j / 10_000_000.0)
        - 0.08 * (obj.rotor_mass_kg / 10.0)
        - 0.04 * (obj.acoustic_spl_db / 100.0)
        - penalty
    )


def _dominates(left: SystemCandidateResult, right: SystemCandidateResult) -> bool:
    a = left.objectives
    b = right.objectives
    weak = (
        a.expected_shaft_energy_j <= b.expected_shaft_energy_j
        and a.rotor_mass_kg <= b.rotor_mass_kg
        and a.acoustic_spl_db <= b.acoustic_spl_db
        and a.worst_mission_efficiency >= b.worst_mission_efficiency
        and a.minimum_safety_factor >= b.minimum_safety_factor
        and a.robust_feasible_probability >= b.robust_feasible_probability
        and a.safe_continuation_fraction >= b.safe_continuation_fraction
    )
    strict = (
        a.expected_shaft_energy_j < b.expected_shaft_energy_j
        or a.rotor_mass_kg < b.rotor_mass_kg
        or a.acoustic_spl_db < b.acoustic_spl_db
        or a.worst_mission_efficiency > b.worst_mission_efficiency
        or a.minimum_safety_factor > b.minimum_safety_factor
        or a.robust_feasible_probability > b.robust_feasible_probability
        or a.safe_continuation_fraction > b.safe_continuation_fraction
    )
    return weak and strict


def _pareto(results: Sequence[SystemCandidateResult]) -> tuple[SystemCandidateResult, ...]:
    feasible = [item for item in results if item.feasible]
    return tuple(
        item for item in feasible
        if not any(_dominates(other, item) for other in feasible if other is not item)
    )


def _chain_digest(campaign_id: str, events: Iterable[EvidenceEvent]) -> str:
    digest = _digest({"campaign_id": campaign_id, "domain": "omega-propulsion-r04-evidence-chain"})
    for event in sorted(events, key=lambda item: (item.frontier_index, STAGE_ORDER[item.stage])):
        event.validate()
        digest = hashlib.sha256(
            f"{digest}:{event.frontier_index}:{event.stage}:{event.evidence_hash}".encode("ascii")
        ).hexdigest()
    return digest


def _m_minus(candidates: Sequence[MultiFidelityCandidate]) -> tuple[MMinusRecord, ...]:
    grouped: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for item in candidates:
        for reason in item.f0.rejection_reasons:
            grouped.setdefault(("F0_ANALYTIC", reason), []).append(
                (item.f0.vector.frontier_index, item.f0.vector.candidate_id)
            )
        for stage, result in (("F1_SYSTEM", item.f1), ("F2_STRESS", item.f2)):
            if result is not None:
                for reason in result.violations:
                    grouped.setdefault((stage, reason), []).append(
                        (item.f0.vector.frontier_index, item.f0.vector.candidate_id)
                    )
    records = []
    for (stage, reason), values in sorted(grouped.items()):
        indices = [item[0] for item in values]
        ids = tuple(item[1] for item in values[:5])
        records.append(
            MMinusRecord(
                signature=_digest({"stage": stage, "reason": reason}),
                stage=stage,
                reason=reason,
                count=len(values),
                first_frontier_index=min(indices),
                last_frontier_index=max(indices),
                sample_candidate_ids=ids,
            )
        )
    return tuple(records)


def plan_shards(
    *,
    campaign_id: str,
    start_index: int,
    count: int,
    shard_count: int,
) -> tuple[ShardManifest, ...]:
    if not campaign_id.strip() or start_index < 0 or count < 1 or shard_count < 1:
        raise ValueError("invalid shard planning request")
    actual = min(count, shard_count)
    base, remainder = divmod(count, actual)
    manifests: list[ShardManifest] = []
    cursor = start_index
    for shard_id in range(actual):
        shard_size = base + (1 if shard_id < remainder else 0)
        seed = _digest(
            {
                "campaign_id": campaign_id,
                "shard_id": shard_id,
                "start_index": cursor,
                "count": shard_size,
            }
        )
        manifests.append(ShardManifest(campaign_id, shard_id, cursor, shard_size, seed))
        cursor += shard_size
    return tuple(manifests)


def run_multifidelity_campaign(
    base_design: RotorDesign,
    medium: FluidMedium,
    mission: MissionGenome,
    *,
    campaign_id: str,
    start_index: int,
    count: int,
    resources: ResourceEnvelope,
    frontier: InfiniteSystemFrontier | None = None,
    atlas: MaterialAtlas | None = None,
    constraints: SystemSearchConstraints | None = None,
    policy: MultiFidelityPolicy | None = None,
    registry: PolarRegistry | None = None,
) -> MultiFidelityCampaignReport:
    if not campaign_id.strip() or start_index < 0 or count < 1:
        raise ValueError("campaign_id, non-negative start_index and positive count are required")
    resources.validate()
    pol = policy or MultiFidelityPolicy()
    pol.validate()
    search_frontier = frontier or InfiniteSystemFrontier(namespace="omega-propulsion-r04")
    material_atlas = atlas or default_material_atlas()
    cfg = constraints or SystemSearchConstraints()
    cfg.validate()

    consumed = 0.0
    candidates: list[MultiFidelityCandidate] = []
    promotions: list[PromotionDecision] = []
    events: list[EvidenceEvent] = []
    checkpoints: list[MultiFidelityCheckpoint] = []
    stop_reason = "requested_batch_completed"

    for offset in range(count):
        index = start_index + offset
        if consumed + pol.f0.cost_units > resources.max_cost_units:
            stop_reason = "resource_budget_exhausted_before_f0"
            break
        vector = search_frontier.vector_at(index, material_atlas)
        f0 = screen_f0(
            base_design,
            medium,
            mission,
            vector,
            atlas=material_atlas,
            constraints=cfg,
            policy=pol,
        )
        consumed += pol.f0.cost_units
        events.append(EvidenceEvent(index, vector.candidate_id, "F0_ANALYTIC", f0.evidence_hash))

        f1: SystemCandidateResult | None = None
        f2: SystemCandidateResult | None = None
        resource_limited = False
        promote_f1 = f0.passed and f0.utility >= pol.f1_utility_threshold
        reason_f1 = "candidate-local F0 gate passed" if promote_f1 else (
            "F0 rejected" if not f0.passed else "F0 utility below threshold"
        )
        if promote_f1 and consumed + pol.f1.cost_units > resources.max_cost_units:
            promote_f1 = False
            resource_limited = True
            reason_f1 = "resource envelope prevented F1 evaluation"
            stop_reason = "resource_budget_limited_promotions"
        promotions.append(
            PromotionDecision(
                vector.candidate_id,
                index,
                "F0_ANALYTIC",
                "F1_SYSTEM",
                promote_f1,
                f0.utility,
                pol.f1_utility_threshold,
                reason_f1,
            )
        )
        if promote_f1:
            f1 = evaluate_system_candidate(
                base_design,
                medium,
                mission,
                vector,
                atlas=material_atlas,
                constraints=cfg,
                registry=registry,
            )
            consumed += pol.f1.cost_units
            events.append(EvidenceEvent(index, vector.candidate_id, "F1_SYSTEM", f1.evidence_hash))

        f1_score = -999.0 if f1 is None else _candidate_score(f1)
        promote_f2 = f1 is not None and (f1.feasible or f1_score >= pol.f2_score_threshold)
        reason_f2 = "F1 feasible or score above stress threshold" if promote_f2 else (
            "F1 not evaluated" if f1 is None else "F1 evidence below stress threshold"
        )
        if promote_f2 and consumed + pol.f2.cost_units > resources.max_cost_units:
            promote_f2 = False
            resource_limited = True
            reason_f2 = "resource envelope prevented F2 stress evaluation"
            stop_reason = "resource_budget_limited_promotions"
        promotions.append(
            PromotionDecision(
                vector.candidate_id,
                index,
                "F1_SYSTEM",
                "F2_STRESS",
                promote_f2,
                f1_score,
                pol.f2_score_threshold,
                reason_f2,
            )
        )
        if promote_f2:
            f2 = evaluate_system_candidate(
                base_design,
                medium,
                mission,
                vector,
                atlas=material_atlas,
                constraints=cfg,
                registry=registry,
                uncertainty_cases=expanded_uncertainty_cases(),
                fault_scenarios=expanded_fault_scenarios(),
            )
            consumed += pol.f2.cost_units
            events.append(EvidenceEvent(index, vector.candidate_id, "F2_STRESS", f2.evidence_hash))

        final = f2 or f1
        final_stage = "F2_STRESS" if f2 is not None else ("F1_SYSTEM" if f1 is not None else "F0_ANALYTIC")
        final_score = f0.utility if final is None else _candidate_score(final)
        candidates.append(
            MultiFidelityCandidate(
                f0=f0,
                f1=f1,
                f2=f2,
                final_stage=final_stage,
                final_score=final_score,
                promoted_to_f1=f1 is not None,
                promoted_to_f2=f2 is not None,
                resource_limited=resource_limited,
            )
        )

        if len(candidates) % resources.checkpoint_interval == 0 or len(candidates) == count:
            checkpoints.append(
                MultiFidelityCheckpoint(
                    next_index=index + 1,
                    evidence_event_count=len(events),
                    consumed_cost_units=consumed,
                    chain_digest=_chain_digest(campaign_id, events),
                )
            )

    next_index = start_index + len(candidates)
    if candidates and (not checkpoints or checkpoints[-1].next_index != next_index):
        checkpoints.append(
            MultiFidelityCheckpoint(
                next_index=next_index,
                evidence_event_count=len(events),
                consumed_cost_units=consumed,
                chain_digest=_chain_digest(campaign_id, events),
            )
        )

    final_results = [item.final_result for item in candidates if item.final_result is not None]
    pareto = _pareto(final_results)
    best = max(final_results, key=_candidate_score) if final_results else None
    remaining = max(0.0, resources.max_cost_units - consumed)
    average_cost = consumed / max(len(candidates), 1)
    recommended = max(1, int(resources.max_cost_units / max(average_cost, pol.f0.cost_units)))
    pressure = consumed / resources.max_cost_units
    backpressure = BackpressureState(
        requested_count=count,
        admitted_f0_count=len(candidates),
        f1_count=sum(item.f1 is not None for item in candidates),
        f2_count=sum(item.f2 is not None for item in candidates),
        consumed_cost_units=consumed,
        remaining_cost_units=remaining,
        pressure_ratio=pressure,
        next_recommended_count=recommended,
        stop_reason=stop_reason,
    )
    return MultiFidelityCampaignReport(
        campaign_id=campaign_id,
        start_index=start_index,
        requested_count=count,
        next_index=next_index,
        candidates=tuple(candidates),
        promotions=tuple(promotions),
        evidence_events=tuple(events),
        pareto_front=pareto,
        best=best,
        m_minus=_m_minus(candidates),
        checkpoints=tuple(checkpoints),
        consumed_cost_units=consumed,
        final_chain_digest=_chain_digest(campaign_id, events),
        backpressure=backpressure,
        policy=pol,
        resources=resources,
        frontier=search_frontier,
    )


def merge_shard_reports(
    reports: Sequence[MultiFidelityCampaignReport],
    *,
    campaign_id: str,
) -> MergedShardReport:
    if not reports:
        raise ValueError("at least one shard report is required")
    ordered = sorted(reports, key=lambda item: item.start_index)
    if any(item.campaign_id != campaign_id for item in ordered):
        raise ValueError("campaign_id mismatch across shards")
    cursor = ordered[0].start_index
    candidate_ids: set[str] = set()
    all_candidates: list[MultiFidelityCandidate] = []
    all_events: list[EvidenceEvent] = []
    for report in ordered:
        if report.start_index != cursor:
            raise ValueError("shard reports must be contiguous and non-overlapping")
        for candidate in report.candidates:
            candidate_id = candidate.f0.vector.candidate_id
            if candidate_id in candidate_ids:
                raise ValueError("duplicate candidate across shard reports")
            candidate_ids.add(candidate_id)
            all_candidates.append(candidate)
        all_events.extend(report.evidence_events)
        cursor = report.next_index
    final_results = [item.final_result for item in all_candidates if item.final_result is not None]
    pareto = _pareto(final_results)
    best = max(final_results, key=_candidate_score) if final_results else None
    return MergedShardReport(
        campaign_id=campaign_id,
        start_index=ordered[0].start_index,
        next_index=cursor,
        shard_count=len(ordered),
        evaluated_count=len(all_candidates),
        evidence_event_count=len(all_events),
        final_chain_digest=_chain_digest(campaign_id, all_events),
        pareto_front=pareto,
        best=best,
        m_minus=_m_minus(all_candidates),
    )
