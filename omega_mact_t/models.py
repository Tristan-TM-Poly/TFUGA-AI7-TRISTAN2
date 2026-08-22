from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class EpistemicType(str, Enum):
    OBSERVED = "OBSERVED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    HYPOTHESIZED = "HYPOTHESIZED"
    UNKNOWN = "UNKNOWN"


class Decision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    HOLD = "HOLD"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ResourceVector:
    action: float = 0.0
    compute: float = 0.0
    memory_persistent: float = 0.0
    observation: float = 0.0
    human_attention: float = 0.0
    time: float = 0.0
    persistent_complexity: float = 0.0
    risk: float = 0.0
    irreversibility: float = 0.0

    def __post_init__(self) -> None:
        for name, value in self.as_dict().items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

    def as_dict(self) -> Dict[str, float]:
        return {
            "action": self.action,
            "compute": self.compute,
            "memory_persistent": self.memory_persistent,
            "observation": self.observation,
            "human_attention": self.human_attention,
            "time": self.time,
            "persistent_complexity": self.persistent_complexity,
            "risk": self.risk,
            "irreversibility": self.irreversibility,
        }

    def weighted_cost(self, weights: Dict[str, float]) -> float:
        return sum(weights.get(key, 1.0) * value for key, value in self.as_dict().items())

    def dominates(self, other: "ResourceVector") -> bool:
        mine, theirs = self.as_dict(), other.as_dict()
        no_worse = all(mine[k] <= theirs[k] for k in mine)
        strictly_better = any(mine[k] < theirs[k] for k in mine)
        return no_worse and strictly_better


@dataclass(frozen=True)
class EvidenceRef:
    id: str
    epistemic_type: EpistemicType
    scope: str
    independent: bool = False


@dataclass(frozen=True)
class VerificationContract:
    required_scope: str
    min_evidence_count: int = 1
    require_independent_verification: bool = True
    require_rollback_if_reversible: bool = True
    max_risk: float = 1.0
    max_irreversibility: float = 1.0


@dataclass(frozen=True)
class TransformationCandidate:
    id: str
    operation: str
    semantic_effect: str
    resources: ResourceVector
    evidence: List[EvidenceRef] = field(default_factory=list)
    generator_role: str = "generator"
    judge_role: str = "judge"
    authority_granted: bool = False
    rollback: Optional[str] = None
    expected_verified_gain: float = 0.0
    expected_future_work_avoided: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    reason: str


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    decision: Decision
    gates: List[GateResult]
    scalar_cost: float
    pareto_dominated: bool = False


@dataclass(frozen=True)
class MactReceipt:
    id: str
    candidate_id: str
    operation: str
    input_state_ref: str
    output_state_ref: str
    resources: ResourceVector
    evidence_ids: List[str]
    gate_results: List[GateResult]
    decision: Decision
    provenance: str
    rollback: Optional[str]
    external_action_performed: bool = False
    auto_promoted: bool = False
