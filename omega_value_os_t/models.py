"""Typed contracts for Ω-VALUE-OS-T∞.

Scores are bounded engineering/governance heuristics. They are never probabilities of
truth, legal conclusions, safety certifications, scientific validation or market value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping


class ValueDimension(str, Enum):
    TRUTH = "truth"
    EVIDENCE = "evidence"
    FERTILITY = "fertility"
    LEARNING = "learning"
    CRYSTALLIZATION = "crystallization"
    SOVEREIGNTY = "sovereignty"
    UTILITY = "utility"
    PROTECTION = "protection"
    GENERATIVITY = "generativity"
    EXTERNAL_VALUE = "external_value"
    SIMPLICITY = "simplicity"
    TESTABILITY = "testability"
    MAINTAINABILITY = "maintainability"
    REUSE = "reuse"


class EvidenceLevel(int, Enum):
    E0_SELF_EVALUATION = 0
    E1_AUTOMATED_TESTS = 1
    E2_INDEPENDENT_BENCHMARK = 2
    E3_EXTERNAL_USER = 3
    E4_EXTERNAL_REPLICATION = 4
    E5_REPEATED_EXTERNAL_VALUE = 5


class AutonomyLevel(int, Enum):
    A0_OBSERVE = 0
    A1_RECOMMEND = 1
    A2_DRAFT = 2
    A3_REVERSIBLE_EXECUTION = 3
    A4_BOUNDED_CONSEQUENCE = 4
    A5_HIGH_CONSEQUENCE = 5


class DecisionStatus(str, Enum):
    BLOCKED = "BLOCKED"
    ABSTAIN = "ABSTAIN_MORE_EVIDENCE"
    ELIGIBLE_FOR_EXPERIMENT = "ELIGIBLE_FOR_EXPERIMENT"
    ELIGIBLE_FOR_HUMAN_REVIEW = "ELIGIBLE_FOR_HUMAN_REVIEW"


HARD_GATES = ("integrity", "safety", "legality", "consent", "critical_provenance")
DEBT_KEYS = ("crystallization", "confidence", "technical", "risk")


def _bounded(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContextProfile:
    name: str
    weights: Mapping[str, float]
    evidence_floor: float = 0.35
    human_review_external_evidence_floor: int = 3
    human_review_closure_floor: float = 0.75

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("profile name is required")
        if not self.weights:
            raise ValueError("profile weights are required")
        total = 0.0
        for key, value in self.weights.items():
            if key not in {x.value for x in ValueDimension}:
                raise ValueError(f"unknown value dimension: {key}")
            value = float(value)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"weight {key} must be finite and non-negative")
            total += value
        if total <= 0:
            raise ValueError("at least one profile weight must be positive")
        _bounded("evidence_floor", self.evidence_floor)
        _bounded("human_review_closure_floor", self.human_review_closure_floor)
        if not 0 <= int(self.human_review_external_evidence_floor) <= 5:
            raise ValueError("external evidence floor must be in [0, 5]")


@dataclass(frozen=True)
class ValueCase:
    case_id: str
    title: str
    profile: str
    hard_gates: Mapping[str, bool]
    dimensions: Mapping[str, float]
    debts: Mapping[str, float] = field(default_factory=dict)
    evidence_level: EvidenceLevel = EvidenceLevel.E0_SELF_EVALUATION
    evidence_strength: float = 0.0
    claim_strength: float = 0.0
    closure: float = 0.0
    reuse: float = 0.0
    uncertainty: float = 1.0
    reversibility: float = 1.0
    autonomy_level: AutonomyLevel = AutonomyLevel.A1_RECOMMEND
    human_approval: bool = False
    expected_action_value: float = 0.0
    expected_information_value: float = 0.0
    provenance_refs: tuple[str, ...] = ()
    falsifiers: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.case_id or not self.title or not self.profile:
            raise ValueError("case_id, title and profile are required")
        unknown_gates = set(self.hard_gates) - set(HARD_GATES)
        if unknown_gates:
            raise ValueError(f"unknown hard gates: {sorted(unknown_gates)}")
        missing_gates = set(HARD_GATES) - set(self.hard_gates)
        if missing_gates:
            raise ValueError(f"missing hard gates: {sorted(missing_gates)}")
        valid_dimensions = {x.value for x in ValueDimension}
        unknown_dimensions = set(self.dimensions) - valid_dimensions
        if unknown_dimensions:
            raise ValueError(f"unknown value dimensions: {sorted(unknown_dimensions)}")
        if not self.dimensions:
            raise ValueError("at least one value dimension is required")
        for key, value in self.dimensions.items():
            _bounded(f"dimension.{key}", value)
        unknown_debts = set(self.debts) - set(DEBT_KEYS)
        if unknown_debts:
            raise ValueError(f"unknown debt keys: {sorted(unknown_debts)}")
        for key, value in self.debts.items():
            if not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"debt.{key} must be finite and non-negative")
        for name in (
            "evidence_strength",
            "claim_strength",
            "closure",
            "reuse",
            "uncertainty",
            "reversibility",
            "expected_action_value",
            "expected_information_value",
        ):
            _bounded(name, getattr(self, name))
        if not isinstance(self.evidence_level, EvidenceLevel):
            object.__setattr__(self, "evidence_level", EvidenceLevel(int(self.evidence_level)))
        if not isinstance(self.autonomy_level, AutonomyLevel):
            object.__setattr__(self, "autonomy_level", AutonomyLevel(int(self.autonomy_level)))
        if self.claim_strength > 0 and not self.assumptions:
            raise ValueError("non-zero claims require explicit assumptions")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ValueCase":
        return cls(
            case_id=str(payload["case_id"]),
            title=str(payload["title"]),
            profile=str(payload.get("profile", "research")),
            hard_gates=dict(payload["hard_gates"]),
            dimensions={k: float(v) for k, v in payload["dimensions"].items()},
            debts={k: float(v) for k, v in payload.get("debts", {}).items()},
            evidence_level=EvidenceLevel(int(payload.get("evidence_level", 0))),
            evidence_strength=float(payload.get("evidence_strength", 0.0)),
            claim_strength=float(payload.get("claim_strength", 0.0)),
            closure=float(payload.get("closure", 0.0)),
            reuse=float(payload.get("reuse", 0.0)),
            uncertainty=float(payload.get("uncertainty", 1.0)),
            reversibility=float(payload.get("reversibility", 1.0)),
            autonomy_level=AutonomyLevel(int(payload.get("autonomy_level", 1))),
            human_approval=bool(payload.get("human_approval", False)),
            expected_action_value=float(payload.get("expected_action_value", 0.0)),
            expected_information_value=float(payload.get("expected_information_value", 0.0)),
            provenance_refs=tuple(str(x) for x in payload.get("provenance_refs", ())),
            falsifiers=tuple(str(x) for x in payload.get("falsifiers", ())),
            assumptions=tuple(str(x) for x in payload.get("assumptions", ())),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "profile": self.profile,
            "hard_gates": dict(sorted(self.hard_gates.items())),
            "dimensions": dict(sorted(self.dimensions.items())),
            "debts": dict(sorted(self.debts.items())),
            "evidence_level": int(self.evidence_level),
            "evidence_strength": self.evidence_strength,
            "claim_strength": self.claim_strength,
            "closure": self.closure,
            "reuse": self.reuse,
            "uncertainty": self.uncertainty,
            "reversibility": self.reversibility,
            "autonomy_level": int(self.autonomy_level),
            "human_approval": self.human_approval,
            "expected_action_value": self.expected_action_value,
            "expected_information_value": self.expected_information_value,
            "provenance_refs": list(self.provenance_refs),
            "falsifiers": list(self.falsifiers),
            "assumptions": list(self.assumptions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DecisionReport:
    case_id: str
    status: DecisionStatus
    profile: str
    hard_gate_passed: bool
    failed_gates: tuple[str, ...]
    warnings: tuple[str, ...]
    soft_score: float
    debt_penalty: float
    external_evidence_factor: float
    closure_factor: float
    reuse_factor: float
    effective_value: float
    claim_ceiling: float
    claim_ceiling_respected: bool
    authority: str
    human_review_required: bool
    next_action: str
    input_digest: str
    report_digest: str = ""

    def payload(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "case_id": self.case_id,
            "status": self.status.value,
            "profile": self.profile,
            "hard_gate_passed": self.hard_gate_passed,
            "failed_gates": list(self.failed_gates),
            "warnings": list(self.warnings),
            "soft_score": self.soft_score,
            "debt_penalty": self.debt_penalty,
            "external_evidence_factor": self.external_evidence_factor,
            "closure_factor": self.closure_factor,
            "reuse_factor": self.reuse_factor,
            "effective_value": self.effective_value,
            "claim_ceiling": self.claim_ceiling,
            "claim_ceiling_respected": self.claim_ceiling_respected,
            "authority": self.authority,
            "human_review_required": self.human_review_required,
            "next_action": self.next_action,
            "input_digest": self.input_digest,
            "scores_are_probabilities": False,
            "automatic_merge_allowed": False,
            "automatic_publication_allowed": False,
            "external_action_performed": False,
        }
        if include_digest:
            value["report_digest"] = self.report_digest
        return value
