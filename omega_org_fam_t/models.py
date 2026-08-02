"""Core immutable models for Ω-ORG-FAM-T."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FamilyCoordinate:
    skeleton: str
    functional_family: str
    electronic_class: str
    reaction_archetype: str
    stereo_class: str
    environment: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FamilyCell:
    id: str
    coordinate: FamilyCoordinate
    compatibility_score: float
    contradictions: tuple[str, ...] = ()
    spectral_markers: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    oak_status: str = "candidate_cell_unvalidated"
    provenance: str = "omega_org_fam_t_default_vocabulary_r01"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coordinate"] = self.coordinate.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class EvidenceTemplate:
    id: str
    family_id: str
    kind: str
    modality: str
    expected: tuple[str, ...]
    contradiction_if: tuple[str, ...] = ()
    status: str = "synthetic_template_not_empirical_evidence"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ClassificationResult:
    ranked_family_ids: list[tuple[str, float]] = field(default_factory=list)
    matched_features: dict[str, list[str]] = field(default_factory=dict)
    rejected_family_ids: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
