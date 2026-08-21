from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence


class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    HEURISTIC = "HEURISTIC"
    CONJECTURED = "CONJECTURED"
    PROVEN = "PROVEN"


class ResidualKind(str, Enum):
    CLIMATE = "CLIMATE"
    WATER = "WATER"
    SOIL = "SOIL"
    BIODIVERSITY = "BIODIVERSITY"
    TOXICITY = "TOXICITY"
    MATERIAL = "MATERIAL"
    WASTE = "WASTE"
    HEAT = "HEAT"
    NOISE = "NOISE"
    SOCIAL = "SOCIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EnvironmentalState:
    state_id: str
    scale: str
    observed_at: str
    indicators: Mapping[str, float] = field(default_factory=dict)
    provenance: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.state_id.strip():
            raise ValueError("state_id must be non-empty")
        if not self.scale.strip():
            raise ValueError("scale must be non-empty")
        if not self.observed_at.strip():
            raise ValueError("observed_at must be non-empty")


@dataclass(frozen=True)
class ResidualPassport:
    residual_id: str
    kind: ResidualKind
    magnitude: float
    unit: str
    origin: str
    transformation: str
    destination: str
    spatial_boundary: str
    temporal_boundary: str
    uncertainty: float = 0.0
    persistence_years: float | None = None
    affected_entities: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.magnitude < 0:
            raise ValueError("magnitude must be >= 0")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0, 1]")
        if self.persistence_years is not None and self.persistence_years < 0:
            raise ValueError("persistence_years must be >= 0")


@dataclass(frozen=True)
class EvidenceContract:
    claim_id: str
    claim: str
    status: EvidenceStatus
    sources: Sequence[str]
    boundary: str
    baseline: str
    falsifier: str

    def complete(self) -> bool:
        return all([
            self.claim_id.strip(),
            self.claim.strip(),
            self.boundary.strip(),
            self.baseline.strip(),
            self.falsifier.strip(),
        ])


@dataclass(frozen=True)
class EnvironmentalTransformationGenome:
    transformation_id: str
    state_before: EnvironmentalState
    goal: str
    mechanism: str
    place: str
    time_horizon: str
    affected_entities: Sequence[str]
    residuals: Sequence[ResidualPassport]
    evidence: Sequence[EvidenceContract]
    reversibility: float
    authority_confirmed: bool
    monitoring_required: bool
    local_scope: str
    global_scope: str
    compensation_claimed_as_restoration: bool = False
    simulation_claimed_as_reality: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.reversibility <= 1.0:
            raise ValueError("reversibility must be in [0, 1]")
        for value, label in [
            (self.transformation_id, "transformation_id"),
            (self.goal, "goal"),
            (self.mechanism, "mechanism"),
            (self.place, "place"),
            (self.time_horizon, "time_horizon"),
            (self.local_scope, "local_scope"),
            (self.global_scope, "global_scope"),
        ]:
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")

    def canonical_dict(self) -> dict:
        def normalize(value):
            if isinstance(value, Enum):
                return value.value
            if hasattr(value, "__dataclass_fields__"):
                return {k: normalize(v) for k, v in asdict(value).items()}
            if isinstance(value, Mapping):
                return {str(k): normalize(v) for k, v in sorted(value.items())}
            if isinstance(value, (tuple, list)):
                return [normalize(v) for v in value]
            return value

        return normalize(self)

    def digest(self) -> str:
        payload = json.dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
