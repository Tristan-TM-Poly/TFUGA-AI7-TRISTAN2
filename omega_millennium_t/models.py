"""Typed domain model for Ω-MILLENNIUM-T∞.

The objects in this module deliberately separate mathematical truth, evidence,
formal verification and research priority.  No field named ``probability`` is
allowed to masquerade as a proof status.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, IntEnum
from typing import Any, Iterable, Mapping


class ProblemId(str, Enum):
    POINCARE = "poincare"
    RIEMANN = "riemann"
    P_VS_NP = "p_vs_np"
    NAVIER_STOKES = "navier_stokes"
    YANG_MILLS = "yang_mills"
    HODGE = "hodge"
    BSD = "birch_swinnerton_dyer"


class ProblemStatus(str, Enum):
    SOLVED_BENCHMARK = "solved_benchmark"
    OPEN = "open"


class ClaimKind(str, Enum):
    DEFINITION = "definition"
    KNOWN_THEOREM = "known_theorem"
    EQUIVALENCE = "equivalence"
    LEMMA = "lemma"
    CONJECTURE = "conjecture"
    COUNTEREXAMPLE = "counterexample"
    COMPUTATION = "computation"
    FORMAL_CERTIFICATE = "formal_certificate"
    SOLUTION_CLAIM = "solution_claim"


class EvidenceKind(str, Enum):
    NONE = "none"
    SOURCE = "source"
    SYMBOLIC = "symbolic"
    NUMERICAL = "numerical"
    RESTRICTED_PROOF = "restricted_proof"
    MANUSCRIPT_PROOF = "manuscript_proof"
    FORMAL_PROOF = "formal_proof"
    INDEPENDENT_REVIEW = "independent_review"


class OAKLevel(IntEnum):
    INTUITION = 0
    WELL_TYPED = 1
    KNOWN_CASES = 2
    NUMERICALLY_TESTED = 3
    RESTRICTED_PROOF = 4
    GENERAL_MANUSCRIPT = 5
    FORMALIZED = 6
    INDEPENDENTLY_REVIEWED = 7


class EdgeKind(str, Enum):
    IMPLIES = "implies"
    EQUIVALENT = "equivalent"
    SPECIALIZES = "specializes"
    GENERALIZES = "generalizes"
    USES = "uses"
    REFUTES = "refutes"
    CERTIFIES = "certifies"


@dataclass(frozen=True)
class ProblemSpec:
    problem_id: ProblemId
    title: str
    status: ProblemStatus
    domain: tuple[str, ...]
    statement: str
    accepted_outcomes: tuple[str, ...]
    canonical_objects: tuple[str, ...]
    barriers: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
    benchmark_role: str | None = None

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.title.strip():
            errors.append("title is empty")
        if not self.statement.strip():
            errors.append("statement is empty")
        if not self.domain:
            errors.append("domain is empty")
        if not self.accepted_outcomes:
            errors.append("accepted outcomes are empty")
        if len(set(self.accepted_outcomes)) != len(self.accepted_outcomes):
            errors.append("accepted outcomes contain duplicates")
        if self.status == ProblemStatus.SOLVED_BENCHMARK and not self.benchmark_role:
            errors.append("solved benchmark requires benchmark_role")
        return tuple(errors)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    kind: EvidenceKind
    description: str
    source: str | None = None
    digest: str | None = None
    scope: str = "declared scope only"
    independently_reproduced: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.evidence_id.strip():
            errors.append("evidence_id is empty")
        if not self.description.strip():
            errors.append("description is empty")
        if self.kind in {EvidenceKind.SOURCE, EvidenceKind.INDEPENDENT_REVIEW} and not self.source:
            errors.append(f"{self.kind.value} evidence requires source")
        if self.kind in {EvidenceKind.NUMERICAL, EvidenceKind.FORMAL_PROOF} and not self.digest:
            errors.append(f"{self.kind.value} evidence requires digest")
        return tuple(errors)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    problem_id: ProblemId
    kind: ClaimKind
    statement: str
    assumptions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    oak_level: OAKLevel = OAKLevel.INTUITION
    scope: str = "unrestricted"
    author_notes: str = ""

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.claim_id.strip():
            errors.append("claim_id is empty")
        if not self.statement.strip():
            errors.append("statement is empty")
        if self.claim_id in self.dependencies:
            errors.append("claim cannot depend on itself")
        if len(set(self.dependencies)) != len(self.dependencies):
            errors.append("duplicate dependencies")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            errors.append("duplicate evidence ids")
        return tuple(errors)

    def with_level(self, level: OAKLevel) -> "Claim":
        return replace(self, oak_level=level)


@dataclass(frozen=True)
class ProofEdge:
    edge_id: str
    problem_id: ProblemId
    premises: tuple[str, ...]
    conclusion: str
    kind: EdgeKind = EdgeKind.IMPLIES
    justification: str = ""
    evidence_ids: tuple[str, ...] = ()
    oak_level: OAKLevel = OAKLevel.INTUITION

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.edge_id.strip():
            errors.append("edge_id is empty")
        if not self.premises:
            errors.append("proof edge requires at least one premise")
        if not self.conclusion.strip():
            errors.append("proof edge conclusion is empty")
        if self.conclusion in self.premises:
            errors.append("conclusion repeats a premise")
        if len(set(self.premises)) != len(self.premises):
            errors.append("duplicate premises")
        return tuple(errors)


@dataclass(frozen=True)
class CounterexampleRecord:
    counterexample_id: str
    claim_id: str
    witness: Mapping[str, Any]
    explanation: str
    reproducible: bool
    digest: str


@dataclass(frozen=True)
class StrategyScore:
    strategy_id: str
    problem_id: ProblemId
    fertility: float
    testability: float
    formalizability: float
    novelty: float
    expected_impact: float
    cost: float
    uncertainty: float
    false_progress_risk: float
    prior_weight: float = 1.0
    evidence_for: int = 0
    evidence_against: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "fertility",
            "testability",
            "formalizability",
            "novelty",
            "expected_impact",
            "cost",
            "uncertainty",
            "false_progress_risk",
            "prior_weight",
        ):
            value = float(getattr(self, field_name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be in [0, 1]")
        if self.evidence_for < 0 or self.evidence_against < 0:
            raise ValueError("evidence counts must be non-negative")

    @property
    def posterior_weight(self) -> float:
        # Beta-like bounded routing weight.  It is not a probability that the
        # mathematical strategy is correct.
        alpha = 1.0 + self.evidence_for
        beta = 1.0 + self.evidence_against
        return self.prior_weight * alpha / (alpha + beta)

    @property
    def value(self) -> float:
        numerator = (
            self.fertility
            * self.testability
            * self.formalizability
            * self.expected_impact
            * max(self.novelty, 0.05)
            * self.posterior_weight
        )
        denominator = max(
            0.025,
            (0.2 + self.cost)
            * (0.2 + self.uncertainty)
            * (0.2 + self.false_progress_risk),
        )
        return numerator / denominator


@dataclass(frozen=True)
class CampaignAllocation:
    strategy_id: str
    problem_id: ProblemId
    rank: int
    normalized_share: float
    finite_budget_units: int
    rationale: tuple[str, ...]


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OAKDecision:
    claim_id: str
    current_level: OAKLevel
    maximum_allowed_level: OAKLevel
    accepted: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_summary: Mapping[str, int]


@dataclass(frozen=True)
class FormalSkeleton:
    language: str
    theorem_name: str
    text: str
    unresolved_obligations: tuple[str, ...]
    proof_complete: bool = False


def unique_nonempty(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    normalized = tuple(value.strip() for value in values if value.strip())
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must be unique")
    return normalized
