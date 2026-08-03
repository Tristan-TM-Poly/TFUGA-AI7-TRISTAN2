"""Typed research objects for Ω-VLA-T∞² R0.2-MAX."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


class EpistemicStatus(str, Enum):
    """Promotion ladder used by generated mathematical artifacts."""

    IDEA = "IDEA"
    DEFINED = "DEFINED"
    NUMERICALLY_OBSERVED = "NUMERICALLY_OBSERVED"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    PROPOSITION = "PROPOSITION"
    PROVED_BY_HAND = "PROVED_BY_HAND"
    FORMALIZED_INCOMPLETE = "FORMALIZED_INCOMPLETE"
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"
    REPRODUCED = "REPRODUCED"
    CANONICAL = "CANONICAL"


@dataclass(frozen=True)
class ResearchArtifact:
    """Base metadata shared by all generated research artifacts."""

    artifact_id: str
    artifact_type: str
    title: str
    definition: str
    hypotheses: tuple[str, ...] = ()
    relations: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    falsifiers: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    status: EpistemicStatus = EpistemicStatus.DEFINED
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id must be non-empty")
        if not self.artifact_type.strip():
            raise ValueError("artifact_type must be non-empty")
        if not self.definition.strip():
            raise ValueError("definition must be non-empty")
        if self.status in {
            EpistemicStatus.FORMALLY_VERIFIED,
            EpistemicStatus.CANONICAL,
        } and not self.tests:
            raise ValueError("promoted artifacts require explicit tests")
        if self.theorem_claimed and self.status not in {
            EpistemicStatus.PROVED_BY_HAND,
            EpistemicStatus.FORMALLY_VERIFIED,
            EpistemicStatus.REPRODUCED,
            EpistemicStatus.CANONICAL,
        }:
            raise ValueError("theorem claims require a proof-level status")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["metadata"] = dict(self.metadata)
        return payload

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObjectGenome:
    """Minimal machine-readable identity card for a mathematical object."""

    object_id: str
    object_type: str
    scalar_system: str
    ambient_space: str
    dimension: str
    basis: str
    metric: str
    symmetries: tuple[str, ...]
    invariants: tuple[str, ...]
    uncertainties: tuple[str, ...]
    residuals: tuple[str, ...]
    epistemic_status: EpistemicStatus = EpistemicStatus.DEFINED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["epistemic_status"] = self.epistemic_status.value
        return payload


@dataclass(frozen=True)
class OperatorGenome:
    """Structural and numerical identity card for an operator."""

    operator_id: str
    operator_class: str
    domain: str
    codomain: str
    linearity: str
    locality: str
    boundedness: str
    adjoint_class: str
    sparsity_class: str
    kernel_description: str
    image_description: str
    spectrum_description: str
    conditioning_risk: str
    conserved_quantities: tuple[str, ...]
    failure_modes: tuple[str, ...]
    required_audits: tuple[str, ...]
    epistemic_status: EpistemicStatus = EpistemicStatus.DEFINED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["epistemic_status"] = self.epistemic_status.value
        return payload


@dataclass(frozen=True)
class ProblemCell:
    """One falsifiable research-program cell."""

    cell_id: str
    address: str
    object_family: str
    hypotheses: tuple[str, ...]
    candidate_conclusion: str
    invariants: tuple[str, ...]
    baselines: tuple[str, ...]
    methods: tuple[str, ...]
    falsifiers: tuple[str, ...]
    expected_artifacts: tuple[str, ...]
    priority: float
    novelty_score: float
    testability_score: float
    risk_score: float
    status: EpistemicStatus = EpistemicStatus.PROPOSITION
    theorem_claimed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "priority",
            "novelty_score",
            "testability_score",
            "risk_score",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.theorem_claimed:
            raise ValueError("factory-generated problem cells cannot claim a theorem")

    def utility_score(self) -> float:
        """A routing heuristic, not truth probability or economic value."""

        return (
            0.35 * self.priority
            + 0.25 * self.novelty_score
            + 0.30 * self.testability_score
            - 0.10 * self.risk_score
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["utility_score"] = self.utility_score()
        return payload


@dataclass(frozen=True)
class SaturationEntry:
    """Persistent M− record for a measured capacity or quality limit."""

    limit_name: str
    observed_at: int
    symptom: str
    evidence: tuple[str, ...]
    lost_work: int
    checkpoint_recovered: bool
    redesign: str
    next_frontier: int | None
    severity: str = "medium"

    def __post_init__(self) -> None:
        if self.observed_at < 0 or self.lost_work < 0:
            raise ValueError("counts cannot be negative")
        if self.next_frontier is not None and self.next_frontier <= 0:
            raise ValueError("next_frontier must be positive when supplied")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_identifier(prefix: str, payload: Mapping[str, Any] | Sequence[Any]) -> str:
    """Create a deterministic, content-addressed identifier."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{prefix}-{sha256(encoded).hexdigest()[:20]}"
