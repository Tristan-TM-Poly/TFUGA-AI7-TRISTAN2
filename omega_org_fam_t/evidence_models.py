"""Immutable evidence objects for Ω-ORG-FAM-T R0.3."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: str
    title: str
    locator: str
    license: str
    retrieved_at: str
    content_sha256: str
    quality: float = 0.5
    source_type: str = "unknown"

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError("source quality must be in [0,1]")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must contain 64 hexadecimal characters")
        int(self.content_sha256, 16)


@dataclass(frozen=True, slots=True)
class Peak:
    position: float
    intensity: float
    tolerance: float
    assignment: str = ""

    def __post_init__(self) -> None:
        if self.tolerance < 0 or self.intensity < 0:
            raise ValueError("peak tolerance and intensity must be non-negative")


@dataclass(frozen=True, slots=True)
class SpectralObservation:
    observation_id: str
    modality: str
    peaks: tuple[Peak, ...]
    source_id: str
    conditions: Mapping[str, str] = field(default_factory=dict)
    preprocessing: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    bundle_id: str
    candidate_families: tuple[str, ...]
    observations: tuple[SpectralObservation, ...]
    sources: tuple[SourceRef, ...]
    formula: str | None = None
    charge: int = 0
    claims: tuple[str, ...] = ()
    status: str = "candidate_evidence_bundle"

    def source_map(self) -> dict[str, SourceRef]:
        result = {source.source_id: source for source in self.sources}
        if len(result) != len(self.sources):
            raise ValueError("source IDs must be unique")
        missing = sorted({obs.source_id for obs in self.observations} - result.keys())
        if missing:
            raise ValueError(f"observations reference missing sources: {missing}")
        return result

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
