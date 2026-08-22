from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Mapping


class FrontierKind(str, Enum):
    LOGICAL = "logical"
    COMPUTATIONAL = "computational"
    ARCHITECTURAL = "architectural"
    REPRESENTATIONAL = "representational"
    INFORMATIONAL = "informational"
    EPISTEMIC = "epistemic"
    UNKNOWN = "unknown"


class FailureKind(str, Enum):
    AXIOM_INSUFFICIENT = "axiom_insufficient"
    REPRESENTATION_INADEQUATE = "representation_inadequate"
    COMPLEXITY_EXCESSIVE = "complexity_excessive"
    INFORMATION_INSUFFICIENT = "information_insufficient"
    PHYSICAL_RESOURCES_INSUFFICIENT = "physical_resources_insufficient"
    OBJECTIVE_UNDERSPECIFIED = "objective_underspecified"
    CONTRADICTION = "contradiction"
    SOLVER_FAILURE = "solver_failure"
    PROOF_ABSENT = "proof_absent"
    UNKNOWN_LIMIT = "unknown_limit"


class TruthLevel(IntEnum):
    IDEA = 0
    CONJECTURE = 1
    INTERNALLY_COHERENT = 2
    NUMERICALLY_VALIDATED = 3
    COUNTERTEST_ROBUST = 4
    MATHEMATICALLY_DERIVED = 5
    KERNEL_VERIFIED = 6
    INDEPENDENTLY_REPLICATED = 7
    ESTABLISHED_IN_DOMAIN = 8


@dataclass(frozen=True)
class CostVector:
    compute: float = 0.0
    proof: float = 0.0
    experiment: float = 0.0
    risk: float = 0.0
    hardware: float = 0.0

    def __post_init__(self) -> None:
        for value in (self.compute, self.proof, self.experiment, self.risk, self.hardware):
            if value < 0:
                raise ValueError("GTNT costs must be non-negative")

    @property
    def total(self) -> float:
        return self.compute + self.proof + self.experiment + self.risk + self.hardware


@dataclass(frozen=True)
class RepresentationCandidate:
    name: str
    sparsity: float
    dimension_cost: float
    compute_cost: float
    reconstruction_error: float
    verifiability: float
    invariant_retention: float

    def __post_init__(self) -> None:
        bounded = (self.sparsity, self.verifiability, self.invariant_retention)
        if any(not 0.0 <= value <= 1.0 for value in bounded):
            raise ValueError("sparsity, verifiability and invariant_retention must lie in [0,1]")
        if any(value < 0 for value in (self.dimension_cost, self.compute_cost, self.reconstruction_error)):
            raise ValueError("representation costs/errors must be non-negative")


@dataclass(frozen=True)
class StrategyPath:
    steps: tuple[str, ...]
    verified_gain: float
    costs: CostVector = field(default_factory=CostVector)
    problem_family: str = "generic"
    representation: str = "unspecified"

    @property
    def signature(self) -> str:
        return "->".join(self.steps)


@dataclass(frozen=True)
class Diagnosis:
    frontier: FrontierKind
    failure: FailureKind
    confidence: float
    rationale: tuple[str, ...]


@dataclass(frozen=True)
class ClaimRecord:
    claim: str
    level: TruthLevel
    provenance: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    countertests: tuple[str, ...] = ()
    uncertainty: Mapping[str, float] = field(default_factory=dict)
    kernel_verified: bool = False
    independent_replications: int = 0
