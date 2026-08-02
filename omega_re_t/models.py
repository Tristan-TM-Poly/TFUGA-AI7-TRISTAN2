"""Typed evidence and experiment models for Ω-RE-T∞.

The package deliberately separates observations, inferences and promoted claims.
No object becomes ``VERIFIED`` merely because a model fits observed traces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
from json import dumps
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence


class ClaimStatus(str, Enum):
    OBSERVED = "OBSERVED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    PLAUSIBLE = "PLAUSIBLE"
    RECONSTRUCTED = "RECONSTRUCTED"
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    UNKNOWN = "UNKNOWN"


class RiskClass(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    PROHIBITED = "prohibited"


class AuthorizationMode(str, Enum):
    OWNED = "owned"
    EXPRESS_PERMISSION = "express_permission"
    OPEN_SPECIFICATION = "open_specification"
    PUBLIC_INTEROPERABILITY = "public_interoperability"
    RESEARCH_SANDBOX = "research_sandbox"


@dataclass(frozen=True, slots=True)
class AuthorizationScope:
    mode: AuthorizationMode
    purpose: str
    permitted_actions: tuple[str, ...]
    prohibited_actions: tuple[str, ...] = ()
    reference: str | None = None

    def allows(self, action: str) -> bool:
        return action in self.permitted_actions and action not in self.prohibited_actions

    def require(self, action: str) -> None:
        if not self.allows(action):
            raise PermissionError(f"Action {action!r} is outside the authorization scope")


@dataclass(frozen=True, slots=True)
class Observation:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    reset_before: bool = True
    source: str = "experiment"
    timestamp: str | None = None
    uncertainty: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.inputs) != len(self.outputs):
            raise ValueError("Inputs and outputs must have the same length")
        if not 0.0 <= self.uncertainty <= 1.0 or not isfinite(self.uncertainty):
            raise ValueError("uncertainty must be a finite probability in [0, 1]")

    @property
    def sequence(self) -> tuple[tuple[str, str], ...]:
        return tuple(zip(self.inputs, self.outputs))


@dataclass(frozen=True, slots=True)
class Experiment:
    inputs: tuple[str, ...]
    expected_information_gain_bits: float
    expected_partition_count: int
    cost: float = 0.0
    risk: RiskClass = RiskClass.MINIMAL
    legal_penalty: float = 0.0
    utility: float = 0.0

    def __post_init__(self) -> None:
        if not self.inputs:
            raise ValueError("An experiment must contain at least one input")
        for value in (
            self.expected_information_gain_bits,
            self.cost,
            self.legal_penalty,
            self.utility,
        ):
            if not isfinite(value):
                raise ValueError("Experiment metrics must be finite")


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate_id: str
    log_likelihood: float
    prior: float
    posterior: float
    complexity: int
    mismatches: int
    status: ClaimStatus = ClaimStatus.INFERRED

    def __post_init__(self) -> None:
        if self.prior < 0.0 or self.posterior < 0.0:
            raise ValueError("Probabilities cannot be negative")
        if self.complexity < 0 or self.mismatches < 0:
            raise ValueError("Counts cannot be negative")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    record_id: str
    kind: str
    payload: Mapping[str, Any]
    claim_status: ClaimStatus
    provenance: tuple[str, ...]
    previous_hash: str
    record_hash: str

    @staticmethod
    def compute_hash(
        *,
        record_id: str,
        kind: str,
        payload: Mapping[str, Any],
        claim_status: ClaimStatus,
        provenance: Sequence[str],
        previous_hash: str,
    ) -> str:
        canonical = dumps(
            {
                "record_id": record_id,
                "kind": kind,
                "payload": payload,
                "claim_status": claim_status.value,
                "provenance": list(provenance),
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["claim_status"] = self.claim_status.value
        return data


@dataclass(frozen=True, slots=True)
class OAKMetricVector:
    fidelity: float
    generalization: float
    causal_quality: float
    parsimony: float
    uncertainty_calibration: float
    reproducibility: float
    legal_provenance: float

    def __post_init__(self) -> None:
        for value in asdict(self).values():
            if not 0.0 <= value <= 1.0 or not isfinite(value):
                raise ValueError("OAK metrics must be finite values in [0, 1]")

    @property
    def minimum(self) -> float:
        return min(asdict(self).values())

    @property
    def geometric_mean(self) -> float:
        values = tuple(asdict(self).values())
        product = 1.0
        for value in values:
            product *= max(value, 1.0e-15)
        return product ** (1.0 / len(values))


@dataclass(frozen=True, slots=True)
class OAKReport:
    decision: str
    metrics: OAKMetricVector
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    promoted_status: ClaimStatus
    evidence_root: str


@dataclass(frozen=True, slots=True)
class CampaignResult:
    rounds: int
    observations: tuple[Observation, ...]
    surviving_candidate_ids: tuple[str, ...]
    posterior_entropy_bits: float
    identifiability_debt_bits: float
    top_candidate_id: str | None
    exact_behavior_recovered: bool
    oak_report: OAKReport | None = None


def ensure_unique(values: Iterable[str], *, label: str) -> tuple[str, ...]:
    result = tuple(values)
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must contain unique values")
    if not result:
        raise ValueError(f"{label} cannot be empty")
    return result
