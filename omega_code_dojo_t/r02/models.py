from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class EvidenceStatus(str, Enum):
    HYPOTHESIS = "hypothesis"
    GENERATED = "generated"
    TESTED = "tested"
    FALSIFIED = "falsified"
    SUPPORTED = "supported"
    CERTIFIED_FIXTURE = "certified_fixture"


class LicenseDecision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class StopReason(str, Enum):
    BUDGET_EXHAUSTED = "budget_exhausted"
    NOVELTY_PLATEAU = "novelty_plateau"
    SAFETY_GATE = "safety_gate"
    COST_GATE = "cost_gate"
    FRONTIER_EXHAUSTED = "frontier_exhausted"
    USER_STOP = "user_stop"


@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    source_type: str
    author: str
    license_id: str
    content_hash: str
    retrieved_at: str
    training_allowed: bool
    redistribution_allowed: bool
    commercial_use_allowed: bool
    attribution_required: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "author": self.author,
            "license_id": self.license_id,
            "content_hash": self.content_hash,
            "retrieved_at": self.retrieved_at,
            "training_allowed": self.training_allowed,
            "redistribution_allowed": self.redistribution_allowed,
            "commercial_use_allowed": self.commercial_use_allowed,
            "attribution_required": self.attribution_required,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ConstraintSpec:
    name: str
    description: str
    severity: str = "required"

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class MetamorphicRelation:
    relation_id: str
    description: str
    transformation: str
    expectation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "relation_id": self.relation_id,
            "description": self.description,
            "transformation": self.transformation,
            "expectation": self.expectation,
        }


@dataclass(frozen=True)
class TaskIR:
    task_id: str
    version: int
    title: str
    domain: str
    archetype: str
    statement: str
    function_name: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    constraints: tuple[ConstraintSpec, ...]
    invariants: tuple[str, ...]
    forbidden_assumptions: tuple[str, ...]
    metamorphic_relations: tuple[MetamorphicRelation, ...]
    mutation_families: tuple[str, ...]
    skill_dependencies: tuple[str, ...]
    difficulty_vector: Mapping[str, float]
    provenance: ProvenanceRecord
    evidence_status: EvidenceStatus = EvidenceStatus.GENERATED
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "version": self.version,
            "title": self.title,
            "domain": self.domain,
            "archetype": self.archetype,
            "statement": self.statement,
            "function_name": self.function_name,
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "constraints": [item.to_dict() for item in self.constraints],
            "invariants": list(self.invariants),
            "forbidden_assumptions": list(self.forbidden_assumptions),
            "metamorphic_relations": [
                item.to_dict() for item in self.metamorphic_relations
            ],
            "mutation_families": list(self.mutation_families),
            "skill_dependencies": list(self.skill_dependencies),
            "difficulty_vector": dict(self.difficulty_vector),
            "provenance": self.provenance.to_dict(),
            "evidence_status": self.evidence_status.value,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class FrontierCell:
    domain: str
    archetype: str
    difficulty_band: str
    language: str
    execution_regime: str
    mutation_family: str

    @property
    def address(self) -> str:
        values = (
            self.domain,
            self.archetype,
            self.difficulty_band,
            self.language,
            self.execution_regime,
            self.mutation_family,
        )
        return "/".join(values)

    def to_dict(self) -> dict[str, str]:
        return {
            "domain": self.domain,
            "archetype": self.archetype,
            "difficulty_band": self.difficulty_band,
            "language": self.language,
            "execution_regime": self.execution_regime,
            "mutation_family": self.mutation_family,
            "address": self.address,
        }


@dataclass(frozen=True)
class SkillPosterior:
    skill_id: str
    alpha: float = 1.0
    beta: float = 1.0
    observations: int = 0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        denominator = (self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1)
        return (self.alpha * self.beta / denominator) ** 0.5

    def observe(self, success: bool, weight: float = 1.0) -> "SkillPosterior":
        if weight <= 0:
            raise ValueError("weight must be positive")
        return SkillPosterior(
            skill_id=self.skill_id,
            alpha=self.alpha + (weight if success else 0.0),
            beta=self.beta + (0.0 if success else weight),
            observations=self.observations + 1,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "alpha": self.alpha,
            "beta": self.beta,
            "observations": self.observations,
            "mean": self.mean,
            "uncertainty": self.uncertainty,
        }


@dataclass(frozen=True)
class CandidateUtility:
    address: str
    information_gain: float
    weakness: float
    transfer: float
    novelty: float
    cost: float
    risk: float
    total: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "address": self.address,
            "information_gain": self.information_gain,
            "weakness": self.weakness,
            "transfer": self.transfer,
            "novelty": self.novelty,
            "cost": self.cost,
            "risk": self.risk,
            "total": self.total,
        }


@dataclass(frozen=True)
class CampaignPolicy:
    materialization_budget: int
    permanent_cap: int | None = None
    novelty_plateau_window: int = 16
    novelty_plateau_threshold: float = 0.01
    stop_on: tuple[str, ...] = (
        StopReason.BUDGET_EXHAUSTED.value,
        StopReason.NOVELTY_PLATEAU.value,
        StopReason.SAFETY_GATE.value,
        StopReason.COST_GATE.value,
    )

    def __post_init__(self) -> None:
        if self.materialization_budget <= 0:
            raise ValueError("materialization_budget must be positive")
        if self.permanent_cap is not None and self.permanent_cap <= 0:
            raise ValueError("permanent_cap must be positive when provided")
        if self.novelty_plateau_window <= 1:
            raise ValueError("novelty_plateau_window must be greater than one")

    def to_dict(self) -> dict[str, Any]:
        return {
            "materialization_budget": self.materialization_budget,
            "permanent_cap": self.permanent_cap,
            "novelty_plateau_window": self.novelty_plateau_window,
            "novelty_plateau_threshold": self.novelty_plateau_threshold,
            "stop_on": list(self.stop_on),
        }


@dataclass(frozen=True)
class CampaignObservation:
    cell: FrontierCell
    task_id: str
    success: bool
    novelty: float
    mutation_score: float
    information_gain: float
    cost_units: int
    evidence_status: EvidenceStatus
    failure_signatures: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell": self.cell.to_dict(),
            "task_id": self.task_id,
            "success": self.success,
            "novelty": self.novelty,
            "mutation_score": self.mutation_score,
            "information_gain": self.information_gain,
            "cost_units": self.cost_units,
            "evidence_status": self.evidence_status.value,
            "failure_signatures": list(self.failure_signatures),
        }


@dataclass(frozen=True)
class CampaignReceipt:
    campaign_id: str
    system_version: str
    logical_frontier_cells: int
    materialized_cells: int
    allocated_units: int
    permanent_total_cap: int | None
    stop_reason: StopReason
    observations: tuple[CampaignObservation, ...]
    skill_posteriors: tuple[SkillPosterior, ...]
    provenance_decisions: Mapping[str, str]
    claims: Mapping[str, bool]
    receipt_sha256: str = field(default="")

    def to_dict(self, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "campaign_id": self.campaign_id,
            "system_version": self.system_version,
            "logical_frontier_cells": self.logical_frontier_cells,
            "materialized_cells": self.materialized_cells,
            "allocated_units": self.allocated_units,
            "permanent_total_cap": self.permanent_total_cap,
            "stop_reason": self.stop_reason.value,
            "observations": [item.to_dict() for item in self.observations],
            "skill_posteriors": [item.to_dict() for item in self.skill_posteriors],
            "provenance_decisions": dict(self.provenance_decisions),
            "claims": dict(self.claims),
        }
        if include_hash:
            payload["receipt_sha256"] = self.receipt_sha256
        return payload
