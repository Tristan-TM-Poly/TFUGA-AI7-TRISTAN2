"""Typed contracts for Ω-POLYGLOT-MULTIVERSE-T∞ R0.2."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping


class CellStatus(str, Enum):
    LOGICAL = "LOGICAL"
    GENERATED = "GENERATED"
    COMPILED = "COMPILED"
    TESTED = "TESTED"
    BENCHMARKED = "BENCHMARKED"
    CERTIFIED = "CERTIFIED"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class NumericalContract:
    absolute_tolerance: float = 1e-12
    relative_tolerance: float = 1e-12
    deterministic: bool = True
    nan_policy: str = "propagate"
    infinity_policy: str = "ieee754"
    signed_zero_sensitive: bool = False

    def validate(self) -> None:
        if self.absolute_tolerance < 0 or self.relative_tolerance < 0:
            raise ValueError("tolerances must be non-negative")
        if self.nan_policy not in {"propagate", "reject", "canonicalize"}:
            raise ValueError(f"unsupported nan policy: {self.nan_policy}")


@dataclass(frozen=True, slots=True)
class AlgorithmSpec:
    algorithm_id: str
    family: str
    operation: str
    arity: int
    rank: int
    dtype: str
    equation: str
    complexity: str
    properties: tuple[str, ...]
    admissible_transformations: tuple[str, ...]
    forbidden_transformations: tuple[str, ...] = ()
    contract: NumericalContract = field(default_factory=NumericalContract)
    schema_version: str = "omega.algorithm-spec.v2"

    def validate(self) -> None:
        if not self.algorithm_id or any(ch.isspace() for ch in self.algorithm_id):
            raise ValueError("algorithm_id must be non-empty and contain no whitespace")
        if self.arity < 0 or self.rank < 0:
            raise ValueError("arity and rank must be non-negative")
        if not self.equation:
            raise ValueError("equation is required")
        self.contract.validate()
        overlap = set(self.admissible_transformations) & set(self.forbidden_transformations)
        if overlap:
            raise ValueError(f"transformations both allowed and forbidden: {sorted(overlap)}")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["properties"] = list(self.properties)
        value["admissible_transformations"] = list(self.admissible_transformations)
        value["forbidden_transformations"] = list(self.forbidden_transformations)
        return value

    @property
    def digest(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class VariantAddress:
    algorithm_id: str
    language: str
    strategy: str
    precision: str
    layout: str
    parallelism: str
    hardware: str
    objective: str
    schema_version: str = "omega.variant-address.v2"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @property
    def variant_id(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return "var_" + sha256(payload).hexdigest()[:24]

    @property
    def uri(self) -> str:
        return (
            f"variant://{self.algorithm_id}/{self.language}/{self.strategy}/"
            f"{self.precision}/{self.layout}/{self.parallelism}/{self.hardware}/{self.objective}"
        )


@dataclass(frozen=True, slots=True)
class MaterializationRecord:
    global_index: int
    variant: VariantAddress
    status: CellStatus
    obligations: tuple[str, ...]
    accepted: bool
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_index": self.global_index,
            "variant_id": self.variant.variant_id,
            "variant_uri": self.variant.uri,
            "variant": self.variant.to_dict(),
            "status": self.status.value,
            "obligations": list(self.obligations),
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    profile_id: str
    system: str
    machine: str
    processor: str
    python: str
    cpu_count: int
    byteorder: str
    features: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["features"] = list(self.features)
        return result


@dataclass(frozen=True, slots=True)
class ScoreVector:
    variant_id: str
    correct: bool
    latency_ns: float
    throughput_per_s: float
    memory_bytes: int
    max_abs_error: float
    compile_ms: float
    portability: float
    safety: float

    def validate(self) -> None:
        if self.latency_ns < 0 or self.memory_bytes < 0 or self.compile_ms < 0:
            raise ValueError("cost metrics must be non-negative")
        if not (0 <= self.portability <= 1 and 0 <= self.safety <= 1):
            raise ValueError("portability and safety must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CampaignManifest:
    campaign_id: str
    frontier_size: int
    start_index: int
    requested_count: int
    next_index: int
    accepted: int
    rejected: int
    duplicate_ids: int
    shards: tuple[Mapping[str, Any], ...]
    status: str = "OAK_LOGICAL_MATERIALIZATION_ONLY"
    permanent_total_cap: None = None
    scientific_validation_claimed: bool = False
    universal_language_winner_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["shards"] = [dict(item) for item in self.shards]
        return result
