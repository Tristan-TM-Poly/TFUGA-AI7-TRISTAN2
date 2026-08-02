from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable, Mapping
import hashlib
import json
import math

class EpistemicStatus(str, Enum):
    ESTABLISHED = "established"
    MEASURED = "measured"
    SIMULATED = "simulated"
    INFERRED = "inferred"
    PROPOSED = "proposed"
    GENERATED = "generated_candidate"
    QUARANTINED = "quarantined"

@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    uncertainty: float | None = None
    status: EpistemicStatus = EpistemicStatus.PROPOSED
    source_id: str | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.value)):
            raise ValueError("quantity value must be finite")
        if not self.unit.strip():
            raise ValueError("quantity unit is required")
        if self.uncertainty is not None:
            if not math.isfinite(float(self.uncertainty)) or self.uncertainty < 0:
                raise ValueError("quantity uncertainty must be finite and non-negative")

@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_type: str
    locator: str
    claim: str
    status: EpistemicStatus
    confidence: float
    method: str = ""
    license: str = "unknown"

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.locator:
            raise ValueError("evidence id and locator are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must lie in [0,1]")

@dataclass(frozen=True)
class U2Tensor:
    aleatoric: float
    epistemic: float
    model_form: float
    measurement: float
    provenance: float
    unknown_unknown: float

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must lie in [0,1]")

    @property
    def aggregate(self) -> float:
        vals = tuple(asdict(self).values())
        return min(1.0, math.sqrt(sum(v*v for v in vals) / len(vals)))

@dataclass(frozen=True)
class CandidateCell:
    candidate_id: str
    campaign_id: str
    logical_index: int
    world_id: str
    world_name: str
    architecture_id: str
    architecture_name: str
    defect_profile_id: str
    process_profile_id: str
    environment_profile_id: str
    mechanism_ids: tuple[str, ...]
    descriptor: Mapping[str, float | int | str | bool]
    required_checks: tuple[str, ...]
    epistemic_status: EpistemicStatus = EpistemicStatus.GENERATED
    provenance_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.logical_index < 0:
            raise ValueError("logical_index must be non-negative")
        if not self.candidate_id or not self.campaign_id:
            raise ValueError("candidate and campaign identifiers are required")
        if len(set(self.mechanism_ids)) != len(self.mechanism_ids):
            raise ValueError("mechanism identifiers must be unique")

    def canonical_payload(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))

    @property
    def fingerprint(self) -> str:
        raw = json.dumps(self.canonical_payload(), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

@dataclass
class SolidGenomeR2:
    genome_id: str
    name: str
    family: str
    composition: dict[str, float]
    bond_vector: dict[str, float]
    structure: dict[str, Any]
    defects: list[dict[str, Any]]
    interfaces: list[dict[str, Any]]
    process_history: list[dict[str, Any]]
    properties: dict[str, Quantity]
    environment: dict[str, Any]
    assumptions: list[str]
    risks: list[str]
    next_experiments: list[str]
    evidence: list[EvidenceRef] = field(default_factory=list)
    uncertainty: U2Tensor = field(default_factory=lambda: U2Tensor(1,1,1,1,1,1))
    status: EpistemicStatus = EpistemicStatus.PROPOSED

    def __post_init__(self) -> None:
        _validate_fraction_map(self.composition, "composition")
        _validate_fraction_map(self.bond_vector, "bond_vector")
        if not self.genome_id or not self.name:
            raise ValueError("genome id and name are required")
        if len(set(self.properties)) != len(self.properties):
            raise ValueError("property names must be unique")

    def canonical_payload(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))

    @property
    def fingerprint(self) -> str:
        raw = json.dumps(self.canonical_payload(), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

@dataclass(frozen=True)
class OAKFinding:
    gate_id: str
    passed: bool
    score: float
    severity: str
    message: str
    evidence: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("gate score must lie in [0,1]")

@dataclass(frozen=True)
class OAKReport:
    object_id: str
    status: str
    aggregate_score: float
    findings: tuple[OAKFinding, ...]
    blockers: tuple[str, ...]
    fingerprint: str


def _validate_fraction_map(values: Mapping[str, float], label: str) -> None:
    if not values:
        raise ValueError(f"{label} cannot be empty")
    if any((not math.isfinite(float(v)) or v < 0) for v in values.values()):
        raise ValueError(f"{label} contains invalid values")
    total = sum(values.values())
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{label} fractions must sum to one, got {total}")


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _canonicalize(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v) for v in value]
    if isinstance(value, float):
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return float(format(value, ".15g"))
    return value
