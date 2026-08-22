from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Residual:
    name: str
    magnitude: float
    uncertainty: float = 0.0
    domain: str = "general"
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.magnitude < 0:
            raise ValueError("residual magnitude must be >= 0")
        if not 0 <= self.uncertainty <= 1:
            raise ValueError("uncertainty must be in [0,1]")


@dataclass(frozen=True)
class GeneratorGenome:
    name: str
    objective: str
    operators: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    budget: int = 8
    meta_depth: int = 0

    @property
    def id(self) -> str:
        return stable_hash(asdict(self))[:16]


@dataclass(frozen=True)
class ArtifactGenome:
    intent: str
    inputs: Mapping[str, Any]
    operators: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    evidence_need: tuple[str, ...] = ()
    rollback: str = "discard candidate"

    @property
    def id(self) -> str:
        return stable_hash(asdict(self))[:16]


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    generator_id: str
    representation: str
    payload: Mapping[str, Any]
    predicted_gain: float
    persistent_complexity: float
    compute_cost: float
    risk: float
    epistemic_debt: float
    simulated: bool = False

    @property
    def utility(self) -> float:
        denominator = self.persistent_complexity + self.compute_cost + self.risk + self.epistemic_debt + 1e-9
        return self.predicted_gain / denominator


@dataclass(frozen=True)
class VerificationResult:
    candidate_id: str
    status: VerificationStatus
    score: float
    residual_after: float
    evidence: tuple[str, ...]
    verifier_id: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Certificate:
    input_hash: str
    output_hash: str
    operator: str
    assumptions: tuple[str, ...]
    tests: tuple[str, ...]
    evidence: tuple[str, ...]
    residual: float
    uncertainty: float
    risk: float
    rollback: str
    verifier_id: str
    version: str = "0.1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def receipt_hash(self) -> str:
        return stable_hash(asdict(self))
