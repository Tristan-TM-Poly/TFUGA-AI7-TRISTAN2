"""Claim-safe data contracts for the Wave 3 Identity Factory."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping
from .assumptions import Assumption
from .expressions import MatrixExpr


class EvidenceState(str, Enum):
    DECLARED = "DECLARED"
    TYPE_CHECKED = "TYPE_CHECKED"
    NUMERICALLY_SUPPORTED = "NUMERICALLY_SUPPORTED"
    FALSIFIED = "FALSIFIED"
    FORMAL_TARGET_EMITTED = "FORMAL_TARGET_EMITTED"
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"


@dataclass(frozen=True)
class IdentitySchema:
    schema_id: str
    title: str
    variables: tuple[str, ...]
    lhs: MatrixExpr
    rhs: MatrixExpr
    assumptions: tuple[Assumption, ...] = ()
    tags: tuple[str, ...] = ()
    parent_ids: tuple[str, ...] = ()
    description: str = ""
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.schema_id or not self.variables:
            raise ValueError("identity schema requires id and variables")
        symbols = set(self.lhs.symbols()) | set(self.rhs.symbols())
        if not symbols.issubset(set(self.variables)):
            raise ValueError(f"undeclared expression symbols: {sorted(symbols-set(self.variables))}")
        if self.theorem_claimed or self.formal_proof_claimed or self.scientific_validation_claimed:
            raise ValueError("generated identity schemas cannot assert proof/validation claims")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "title": self.title,
            "variables": list(self.variables),
            "lhs": self.lhs.to_dict(),
            "rhs": self.rhs.to_dict(),
            "assumptions": [x.to_dict() for x in self.assumptions],
            "tags": list(self.tags),
            "parent_ids": list(self.parent_ids),
            "description": self.description,
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


@dataclass(frozen=True)
class IdentityAddress:
    schema_id: str
    dimension: int
    scalar_system: str
    matrix_family: str
    mutation_policy: str
    trial_profile: str

    def canonical(self) -> str:
        return "|".join(
            (
                f"schema={self.schema_id}", f"dimension={self.dimension}",
                f"scalar={self.scalar_system}", f"family={self.matrix_family}",
                f"mutation={self.mutation_policy}", f"trials={self.trial_profile}",
            )
        )

    def digest(self) -> str:
        return sha256(self.canonical().encode()).hexdigest()


@dataclass(frozen=True)
class IdentityInstance:
    instance_id: str
    address: IdentityAddress
    schema_digest: str
    assumptions: tuple[Assumption, ...]
    mutation_notes: tuple[str, ...] = ()
    evidence_state: EvidenceState = EvidenceState.DECLARED
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "address": asdict(self.address),
            "schema_digest": self.schema_digest,
            "assumptions": [x.to_dict() for x in self.assumptions],
            "mutation_notes": list(self.mutation_notes),
            "evidence_state": self.evidence_state.value,
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


@dataclass(frozen=True)
class Counterexample:
    counterexample_id: str
    schema_id: str
    dimension: int
    scalar_system: str
    environment: Mapping[str, tuple[tuple[dict[str, float], ...], ...]]
    absolute_residual: float
    relative_residual: float
    assumption_audit: tuple[Mapping[str, Any], ...]
    seed: int
    trial: int
    minimization_steps: int = 0
    repaired_hypotheses: tuple[str, ...] = ()
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IdentityTestReport:
    schema_id: str
    passed: bool
    trials_requested: int
    trials_completed: int
    maximum_absolute_residual: float
    maximum_relative_residual: float
    counterexample: Counterexample | None = None
    state: EvidenceState = EvidenceState.DECLARED
    errors: tuple[str, ...] = ()
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["counterexample"] = (
            None if self.counterexample is None else self.counterexample.to_dict()
        )
        return payload
