from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class InsightKind(str, Enum):
    STRATEGY = "strategy"
    COUNTEREXAMPLE = "counterexample"
    TEST_GAP = "test_gap"
    TRANSFER = "transfer"
    CALIBRATION = "calibration"
    COST = "cost"
    PLATEAU = "plateau"


class PlateauKind(str, Enum):
    NONE = "none"
    NOVELTY = "novelty"
    INFORMATION = "information"
    EFFICIENCY = "efficiency"
    MASTERY = "mastery"
    EVIDENCE = "evidence"


class ActionKind(str, Enum):
    REPAIR_TEST = "repair_test"
    REPAIR_SKILL = "repair_skill"
    CONFIRM_TRANSFER = "confirm_transfer"
    EXPLORE_FRONTIER = "explore_frontier"
    REDUCE_COST = "reduce_cost"
    RECALIBRATE = "recalibrate"


@dataclass(frozen=True)
class ObservationView:
    campaign_id: str
    address: str
    task_id: str
    domain: str
    archetype: str
    language: str
    mutation_family: str
    success: bool
    novelty: float
    mutation_score: float
    information_gain: float
    cost_units: int
    failure_signatures: tuple[str, ...]

    @property
    def skills(self) -> tuple[str, ...]:
        return (
            f"domain:{self.domain}",
            f"archetype:{self.archetype}",
            f"language:{self.language}",
            f"mutation:{self.mutation_family}",
        )

    @property
    def information_efficiency(self) -> float:
        return self.information_gain / max(1, self.cost_units)

    @property
    def test_gap(self) -> float:
        return max(0.0, 1.0 - self.mutation_score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "address": self.address,
            "task_id": self.task_id,
            "domain": self.domain,
            "archetype": self.archetype,
            "language": self.language,
            "mutation_family": self.mutation_family,
            "success": self.success,
            "novelty": self.novelty,
            "mutation_score": self.mutation_score,
            "information_gain": self.information_gain,
            "cost_units": self.cost_units,
            "information_efficiency": self.information_efficiency,
            "failure_signatures": list(self.failure_signatures),
        }


@dataclass(frozen=True)
class SkillLearning:
    skill_id: str
    successes: float
    failures: float
    observations: int
    total_cost: int
    total_information_gain: float
    mutation_gap_sum: float

    @property
    def alpha(self) -> float:
        return 1.0 + self.successes

    @property
    def beta(self) -> float:
        return 1.0 + self.failures

    @property
    def mastery(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        denominator = (self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1)
        return (self.alpha * self.beta / denominator) ** 0.5

    @property
    def weakness(self) -> float:
        return 1.0 - self.mastery

    @property
    def learning_efficiency(self) -> float:
        return self.total_information_gain / max(1, self.total_cost)

    @property
    def mean_test_gap(self) -> float:
        return self.mutation_gap_sum / max(1, self.observations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "successes": self.successes,
            "failures": self.failures,
            "observations": self.observations,
            "mastery": self.mastery,
            "uncertainty": self.uncertainty,
            "weakness": self.weakness,
            "total_cost": self.total_cost,
            "total_information_gain": self.total_information_gain,
            "learning_efficiency": self.learning_efficiency,
            "mean_test_gap": self.mean_test_gap,
        }


@dataclass(frozen=True)
class FailureCluster:
    signature: str
    occurrences: int
    tasks: tuple[str, ...]
    skills: tuple[str, ...]
    mean_information_gain: float
    mean_cost: float
    mean_mutation_gap: float

    @property
    def repair_value(self) -> float:
        recurrence = 1.0 + min(4.0, self.occurrences / 2.0)
        informativeness = 0.25 + self.mean_information_gain
        test_weakness = 1.0 + self.mean_mutation_gap
        return recurrence * informativeness * test_weakness / max(1.0, self.mean_cost)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signature": self.signature,
            "occurrences": self.occurrences,
            "tasks": list(self.tasks),
            "skills": list(self.skills),
            "mean_information_gain": self.mean_information_gain,
            "mean_cost": self.mean_cost,
            "mean_mutation_gap": self.mean_mutation_gap,
            "repair_value": self.repair_value,
        }


@dataclass(frozen=True)
class TransferEdge:
    source_skill: str
    target_skill: str
    supporting_successes: int
    contradicting_failures: int
    distinct_campaigns: int

    @property
    def confidence(self) -> float:
        alpha = 1 + self.supporting_successes
        beta = 1 + self.contradicting_failures
        evidence_factor = min(1.0, self.distinct_campaigns / 3.0)
        return (alpha / (alpha + beta)) * evidence_factor

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_skill": self.source_skill,
            "target_skill": self.target_skill,
            "supporting_successes": self.supporting_successes,
            "contradicting_failures": self.contradicting_failures,
            "distinct_campaigns": self.distinct_campaigns,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class LearningInsight:
    insight_id: str
    kind: InsightKind
    title: str
    claim: str
    evidence: tuple[str, ...]
    score: float
    uncertainty: float
    falsifier: str
    next_experiment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "kind": self.kind.value,
            "title": self.title,
            "claim": self.claim,
            "evidence": list(self.evidence),
            "score": self.score,
            "uncertainty": self.uncertainty,
            "falsifier": self.falsifier,
            "next_experiment": self.next_experiment,
        }


@dataclass(frozen=True)
class PlateauReport:
    kind: PlateauKind
    detected: bool
    recent_window: int
    recent_novelty: float
    recent_information_gain: float
    recent_efficiency: float
    previous_efficiency: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "detected": self.detected,
            "recent_window": self.recent_window,
            "recent_novelty": self.recent_novelty,
            "recent_information_gain": self.recent_information_gain,
            "recent_efficiency": self.recent_efficiency,
            "previous_efficiency": self.previous_efficiency,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LearningAction:
    action_id: str
    kind: ActionKind
    priority: float
    target: str
    rationale: str
    experiment_spec: Mapping[str, Any]
    success_criterion: str
    stop_condition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind.value,
            "priority": self.priority,
            "target": self.target,
            "rationale": self.rationale,
            "experiment_spec": dict(self.experiment_spec),
            "success_criterion": self.success_criterion,
            "stop_condition": self.stop_condition,
        }


@dataclass(frozen=True)
class LearningReport:
    report_id: str
    system_version: str
    receipt_count: int
    observation_count: int
    unique_addresses: int
    logical_frontier_cells: int
    coverage_ratio: float
    success_rate: float
    mean_mutation_score: float
    total_information_gain: float
    total_cost_units: int
    information_efficiency: float
    skills: tuple[SkillLearning, ...]
    failure_clusters: tuple[FailureCluster, ...]
    transfer_edges: tuple[TransferEdge, ...]
    insights: tuple[LearningInsight, ...]
    plateau: PlateauReport
    claims: Mapping[str, bool]
    report_sha256: str = field(default="")

    def to_dict(self, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "report_id": self.report_id,
            "system_version": self.system_version,
            "receipt_count": self.receipt_count,
            "observation_count": self.observation_count,
            "unique_addresses": self.unique_addresses,
            "logical_frontier_cells": self.logical_frontier_cells,
            "coverage_ratio": self.coverage_ratio,
            "success_rate": self.success_rate,
            "mean_mutation_score": self.mean_mutation_score,
            "total_information_gain": self.total_information_gain,
            "total_cost_units": self.total_cost_units,
            "information_efficiency": self.information_efficiency,
            "skills": [item.to_dict() for item in self.skills],
            "failure_clusters": [item.to_dict() for item in self.failure_clusters],
            "transfer_edges": [item.to_dict() for item in self.transfer_edges],
            "insights": [item.to_dict() for item in self.insights],
            "plateau": self.plateau.to_dict(),
            "claims": dict(self.claims),
        }
        if include_hash:
            payload["report_sha256"] = self.report_sha256
        return payload
