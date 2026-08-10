from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from math import log2
from typing import Any, Mapping, Sequence

SEVERITIES = ("low", "medium", "high", "critical")
DIAGNOSIS_STATUSES = ("AMBIGUOUS", "HEURISTICALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "ALL_HYPOTHESES_REFUTED")
FORBIDDEN_CAPABILITIES = frozenset({
    "patch_code", "push_branch", "merge", "release", "publish", "read_secrets",
    "financial_action", "modify_security_policy", "external_side_effect",
})


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(value) for value in values)))


def shannon_entropy(weights: Sequence[float]) -> float:
    total = sum(max(0.0, float(value)) for value in weights)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in weights:
        probability = max(0.0, float(value)) / total
        if probability > 0:
            entropy -= probability * log2(probability)
    return entropy


@dataclass(frozen=True)
class CausalHypothesis:
    hypothesis_id: str
    statement: str
    cause_node_ids: tuple[str, ...]
    prior_weight: float
    assumptions: tuple[str, ...] = ()
    falsifiers: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    severity: str = "medium"

    def __post_init__(self) -> None:
        if not self.hypothesis_id or not self.statement:
            raise ValueError("hypothesis_id and statement are required")
        if self.prior_weight <= 0:
            raise ValueError("prior_weight must be positive")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("cause_node_ids", "assumptions", "falsifiers", "scope"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class CausalObservation:
    observation_id: str
    statement: str
    likelihood_by_hypothesis: Mapping[str, float]
    reliability: float = 1.0
    source_evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id or not self.statement:
            raise ValueError("observation_id and statement are required")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be in [0, 1]")
        if not self.likelihood_by_hypothesis:
            raise ValueError("likelihood_by_hypothesis is required")
        for value in self.likelihood_by_hypothesis.values():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError("observation likelihoods must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "statement": self.statement,
            "likelihood_by_hypothesis": dict(sorted(self.likelihood_by_hypothesis.items())),
            "reliability": self.reliability,
            "source_evidence_ids": list(self.source_evidence_ids),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class HypothesisAssessment:
    hypothesis_id: str
    support_score: float
    rank: int
    evidence_for: tuple[str, ...]
    evidence_against: tuple[str, ...]
    untested_falsifiers: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("evidence_for", "evidence_against", "untested_falsifiers"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class CausalDiagnosis:
    failure_id: str
    assessments: tuple[HypothesisAssessment, ...]
    status: str
    top_hypothesis_id: str | None
    support_gap: float
    prior_entropy: float
    posterior_entropy: float
    information_gain: float
    limitations: tuple[str, ...]
    schema: str = "omega-ci-causal-diagnosis/v4"

    def __post_init__(self) -> None:
        if self.status not in DIAGNOSIS_STATUSES:
            raise ValueError(f"unsupported diagnosis status: {self.status}")

    @property
    def diagnosis_id(self) -> str:
        return f"DIAG-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "assessments": [item.to_dict() for item in self.assessments],
            "status": self.status,
            "top_hypothesis_id": self.top_hypothesis_id,
            "support_gap": round(self.support_gap, 9),
            "prior_entropy": round(self.prior_entropy, 9),
            "posterior_entropy": round(self.posterior_entropy, 9),
            "information_gain": round(self.information_gain, 9),
            "limitations": list(self.limitations),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "diagnosis_id": self.diagnosis_id,
            **self.identity_payload(),
            "causality_proven": False,
            "human_review_required": True,
            "automatic_patch_allowed": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class ExperimentDesign:
    experiment_id: str
    description: str
    outcomes: tuple[str, ...]
    likelihoods: Mapping[str, Mapping[str, float]]
    compute_cost: float
    human_cost: float
    safety_risk: float
    required_capability: str = "run_tests"
    affected_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.experiment_id or not self.description:
            raise ValueError("experiment_id and description are required")
        if len(self.outcomes) < 2:
            raise ValueError("an experiment requires at least two outcomes")
        if min(self.compute_cost, self.human_cost, self.safety_risk) < 0:
            raise ValueError("costs and risk cannot be negative")
        if self.safety_risk > 1:
            raise ValueError("safety_risk must be in [0, 1]")
        outcome_set = set(self.outcomes)
        for hypothesis_id, distribution in self.likelihoods.items():
            if set(distribution) != outcome_set:
                raise ValueError(f"likelihood outcomes mismatch for {hypothesis_id}")
            total = sum(float(value) for value in distribution.values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"outcome likelihoods must sum to 1 for {hypothesis_id}")
            if any(not 0.0 <= float(value) <= 1.0 for value in distribution.values()):
                raise ValueError("experiment likelihoods must be in [0, 1]")

    @property
    def total_cost(self) -> float:
        return self.compute_cost + self.human_cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "description": self.description,
            "outcomes": list(self.outcomes),
            "likelihoods": {
                hypothesis_id: dict(sorted(distribution.items()))
                for hypothesis_id, distribution in sorted(self.likelihoods.items())
            },
            "compute_cost": self.compute_cost,
            "human_cost": self.human_cost,
            "safety_risk": self.safety_risk,
            "required_capability": self.required_capability,
            "affected_claim_ids": list(self.affected_claim_ids),
            "total_cost": round(self.total_cost, 9),
        }


@dataclass(frozen=True)
class ExperimentRecommendation:
    experiment_id: str
    expected_information_gain: float
    utility: float
    cost: float
    safety_risk: float
    expected_outcome_distribution: Mapping[str, float]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "expected_outcome_distribution": dict(sorted(self.expected_outcome_distribution.items())),
        }


@dataclass(frozen=True)
class DiscriminationPlan:
    failure_id: str
    recommendations: tuple[ExperimentRecommendation, ...]
    rejected: Mapping[str, str]
    budget: float
    consumed_budget: float
    expected_information_gain: float
    schema: str = "omega-ci-discrimination-plan/v4"

    @property
    def plan_id(self) -> str:
        return f"DISCRIM-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "recommendations": [item.to_dict() for item in self.recommendations],
            "rejected": dict(sorted(self.rejected.items())),
            "budget": self.budget,
            "consumed_budget": round(self.consumed_budget, 9),
            "expected_information_gain": round(self.expected_information_gain, 9),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan_id": self.plan_id,
            **self.identity_payload(),
            "execution_authorized": False,
            "automatic_patch_allowed": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class ReproductionReceipt:
    failure_id: str
    original_items: tuple[str, ...]
    minimized_items: tuple[str, ...]
    evaluations: int
    preserved_failure: bool
    limit_reached: bool
    reduction_ratio: float
    trace: tuple[Mapping[str, Any], ...]
    schema: str = "omega-ci-minimal-reproduction/v4"

    @property
    def reproduction_id(self) -> str:
        return f"REPRO-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "original_items": list(self.original_items),
            "minimized_items": list(self.minimized_items),
            "evaluations": self.evaluations,
            "preserved_failure": self.preserved_failure,
            "limit_reached": self.limit_reached,
            "reduction_ratio": round(self.reduction_ratio, 9),
            "trace": [dict(item) for item in self.trace],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "reproduction_id": self.reproduction_id,
            **self.identity_payload(),
            "execution_environment": "synthetic_local_fixture",
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class BisectStep:
    candidate_sha: str
    lower_good_sha: str
    upper_bad_sha: str
    remaining_candidates: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BisectPlan:
    failure_id: str
    ordered_commits: tuple[str, ...]
    known_good_sha: str
    known_bad_sha: str
    next_step: BisectStep | None
    maximum_remaining_evaluations: int
    tested_verdicts: Mapping[str, str]
    status: str
    schema: str = "omega-ci-bisect-plan/v4"

    @property
    def plan_id(self) -> str:
        return f"BISECT-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "ordered_commits": list(self.ordered_commits),
            "known_good_sha": self.known_good_sha,
            "known_bad_sha": self.known_bad_sha,
            "next_step": self.next_step.to_dict() if self.next_step else None,
            "maximum_remaining_evaluations": self.maximum_remaining_evaluations,
            "tested_verdicts": dict(sorted(self.tested_verdicts.items())),
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan_id": self.plan_id,
            **self.identity_payload(),
            "execution_authorized": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class CounterfactualWorld:
    hypothesis_id: str
    intervention: str
    predicted_outcomes: Mapping[str, float]
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "intervention": self.intervention,
            "predicted_outcomes": dict(sorted(self.predicted_outcomes.items())),
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True)
class CausalDossier:
    failure_id: str
    diagnosis: CausalDiagnosis
    discrimination_plan: DiscriminationPlan
    reproduction: ReproductionReceipt
    bisect_plan: BisectPlan
    counterfactual_worlds: tuple[CounterfactualWorld, ...]
    unresolved_questions: tuple[str, ...]
    limitations: tuple[str, ...]
    schema: str = "omega-ci-causal-dossier/v4"

    @property
    def dossier_id(self) -> str:
        return f"DOSSIER-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "diagnosis": self.diagnosis.to_dict(),
            "discrimination_plan": self.discrimination_plan.to_dict(),
            "reproduction": self.reproduction.to_dict(),
            "bisect_plan": self.bisect_plan.to_dict(),
            "counterfactual_worlds": [item.to_dict() for item in self.counterfactual_worlds],
            "unresolved_questions": list(self.unresolved_questions),
            "limitations": list(self.limitations),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dossier_id": self.dossier_id,
            **self.identity_payload(),
            "causality_proven": False,
            "execution_authorized": False,
            "automatic_patch_allowed": False,
            "automatic_merge_allowed": False,
            "human_review_required": True,
            "maximum_authority": "A3",
            "remote_mutations": 0,
        }
