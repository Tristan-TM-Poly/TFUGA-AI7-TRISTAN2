"""Claim-safe data contracts for Ω-VLA Wave 4 counterexample research."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


class SearchState(str, Enum):
    PLANNED = "PLANNED"
    SEARCHED_NO_WITNESS = "SEARCHED_NO_WITNESS"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    MINIMIZED = "MINIMIZED"
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    REGRESSION_EMITTED = "REGRESSION_EMITTED"


class EvidenceLevel(str, Enum):
    GENERATED = "GENERATED"
    NUMERICALLY_CHECKED = "NUMERICALLY_CHECKED"
    SYMBOLICALLY_CHECKED = "SYMBOLICALLY_CHECKED"
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class SearchPlan:
    conjecture_id: str
    dimension: int
    scalar_system: str
    family: str
    strategy: str
    minimizer: str
    seed: int
    trials: int
    tolerance: float = 1e-8
    metadata: Mapping[str, Any] = field(default_factory=dict)
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.conjecture_id:
            raise ValueError("conjecture_id is required")
        if self.dimension < 1 or self.trials < 1 or self.tolerance <= 0:
            raise ValueError("dimension, trials and tolerance must be positive")
        if self.scalar_system not in {"real", "complex"}:
            raise ValueError("scalar_system must be real or complex")
        if self.theorem_claimed or self.formal_proof_claimed or self.scientific_validation_claimed:
            raise ValueError("generated search plans cannot claim proof or validation")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return sha256(_canonical_json(self.to_dict()).encode()).hexdigest()


@dataclass(frozen=True)
class MatrixWitness:
    matrices: Mapping[str, tuple[tuple[dict[str, float], ...], ...]]
    absolute_residual: float
    relative_residual: float
    assumptions_passed: bool
    assumption_audit: tuple[Mapping[str, Any], ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.absolute_residual < 0 or self.relative_residual < 0:
            raise ValueError("residuals must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return sha256(_canonical_json(self.to_dict()).encode()).hexdigest()


@dataclass(frozen=True)
class MinimizationTrace:
    method: str
    before_nonzeros: int
    after_nonzeros: int
    before_dimension: int
    after_dimension: int
    accepted_steps: tuple[Mapping[str, Any], ...] = ()
    rejected_steps: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepairProposal:
    proposal_id: str
    conjecture_id: str
    added_hypotheses: tuple[str, ...]
    rationale: tuple[str, ...]
    confidence_label: str
    evidence_level: EvidenceLevel = EvidenceLevel.NUMERICALLY_CHECKED
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def __post_init__(self) -> None:
        if self.confidence_label not in {"low", "medium", "high"}:
            raise ValueError("invalid confidence_label")
        if self.evidence_level == EvidenceLevel.FORMALLY_VERIFIED and not self.formal_proof_claimed:
            raise ValueError("formal evidence requires an explicit verified claim")
        if self.theorem_claimed or self.formal_proof_claimed:
            raise ValueError("Wave 4 generated repairs cannot claim proof")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_level"] = self.evidence_level.value
        return payload


@dataclass(frozen=True)
class CounterexampleRecord:
    record_id: str
    conjecture_id: str
    plan_digest: str
    state: SearchState
    witness: MatrixWitness
    minimization: MinimizationTrace | None = None
    repairs: tuple[RepairProposal, ...] = ()
    regression_source: str | None = None
    tags: tuple[str, ...] = ()
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def __post_init__(self) -> None:
        if self.theorem_claimed or self.formal_proof_claimed or self.scientific_validation_claimed:
            raise ValueError("counterexample records cannot assert theorem/proof/science claims")

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "conjecture_id": self.conjecture_id,
            "plan_digest": self.plan_digest,
            "state": self.state.value,
            "witness": self.witness.to_dict(),
            "minimization": None if self.minimization is None else self.minimization.to_dict(),
            "repairs": [value.to_dict() for value in self.repairs],
            "regression_source": self.regression_source,
            "tags": list(self.tags),
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }

    def digest(self) -> str:
        return sha256(_canonical_json(self.to_dict()).encode()).hexdigest()


@dataclass(frozen=True)
class SearchReport:
    plan: SearchPlan
    state: SearchState
    trials_completed: int
    maximum_relative_residual: float
    record: CounterexampleRecord | None = None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "state": self.state.value,
            "trials_completed": self.trials_completed,
            "maximum_relative_residual": self.maximum_relative_residual,
            "record": None if self.record is None else self.record.to_dict(),
            "errors": list(self.errors),
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }


def make_record_id(conjecture_id: str, plan_digest: str, witness_digest: str) -> str:
    payload = f"{conjecture_id}|{plan_digest}|{witness_digest}"
    return "mminus4-" + sha256(payload.encode()).hexdigest()[:28]


def matrix_to_payload(matrix: Any) -> tuple[tuple[dict[str, float], ...], ...]:
    import numpy as np

    value = np.asarray(matrix, dtype=np.complex128)
    if value.ndim != 2:
        raise ValueError("matrix witness must be two-dimensional")
    return tuple(
        tuple({"real": float(item.real), "imag": float(item.imag)} for item in row)
        for row in value
    )


def payload_to_matrix(payload: Sequence[Sequence[Mapping[str, float]]]) -> Any:
    import numpy as np

    return np.asarray(
        [[complex(float(item["real"]), float(item["imag"])) for item in row] for row in payload],
        dtype=np.complex128,
    )
