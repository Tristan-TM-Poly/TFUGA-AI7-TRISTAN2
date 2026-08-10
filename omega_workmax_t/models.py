from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any


class WorkState(str, Enum):
    DISCOVERED = "DISCOVERED"
    ROUTED = "ROUTED"
    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    EVIDENCED = "EVIDENCED"
    VALIDATED = "VALIDATED"
    CRYSTALLIZED = "CRYSTALLIZED"
    INTEGRATED = "INTEGRATED"
    REUSED = "REUSED"
    DEDUPLICATED = "DEDUPLICATED"
    BLOCKED = "BLOCKED"
    M_MINUS = "M_MINUS"
    SUPERSEDED = "SUPERSEDED"


def _unit(value: float, field_name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def normalize_semantic_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


@dataclass(frozen=True)
class WorkPacket:
    work_id: str
    objective: str
    artifact: str
    dependencies: tuple[str, ...] = ()
    estimated_seconds: float = 1.0
    value: float = 1.0
    evidence_weight: float = 0.5
    crystallization: float = 0.0
    reuse_score: float = 0.0
    risk: float = 0.0
    failure_probability: float = 0.0
    reversible: bool = True
    tags: tuple[str, ...] = ()
    semantic_key: str | None = None
    capability_id: str | None = None
    required_evidence: tuple[str, ...] = ()
    state: WorkState = WorkState.DISCOVERED

    def __post_init__(self) -> None:
        if not self.work_id.strip():
            raise ValueError("work_id cannot be empty")
        if not self.objective.strip():
            raise ValueError("objective cannot be empty")
        if not self.artifact.strip():
            raise ValueError("artifact cannot be empty")
        if self.estimated_seconds <= 0:
            raise ValueError("estimated_seconds must be positive")
        if self.value < 0:
            raise ValueError("value cannot be negative")
        object.__setattr__(self, "dependencies", tuple(dict.fromkeys(self.dependencies)))
        object.__setattr__(self, "tags", tuple(dict.fromkeys(self.tags)))
        object.__setattr__(self, "required_evidence", tuple(dict.fromkeys(self.required_evidence)))
        object.__setattr__(self, "evidence_weight", _unit(self.evidence_weight, "evidence_weight"))
        object.__setattr__(self, "crystallization", _unit(self.crystallization, "crystallization"))
        object.__setattr__(self, "reuse_score", _unit(self.reuse_score, "reuse_score"))
        object.__setattr__(self, "risk", _unit(self.risk, "risk"))
        object.__setattr__(self, "failure_probability", _unit(self.failure_probability, "failure_probability"))
        if self.work_id in self.dependencies:
            raise ValueError("a WorkPacket cannot depend on itself")

    @property
    def semantic_signature(self) -> str:
        if self.semantic_key:
            basis = normalize_semantic_text(self.semantic_key)
        else:
            basis = "|".join(
                [
                    normalize_semantic_text(self.objective),
                    normalize_semantic_text(self.artifact),
                    ",".join(sorted(normalize_semantic_text(tag) for tag in self.tags)),
                ]
            )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    @property
    def content_digest(self) -> str:
        payload = asdict(self)
        payload["state"] = self.state.value
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkPacket":
        data = dict(payload)
        data["dependencies"] = tuple(data.get("dependencies", ()))
        data["tags"] = tuple(data.get("tags", ()))
        data["required_evidence"] = tuple(data.get("required_evidence", ()))
        if "state" in data and not isinstance(data["state"], WorkState):
            data["state"] = WorkState(data["state"])
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["semantic_signature"] = self.semantic_signature
        payload["content_digest"] = self.content_digest
        return payload


@dataclass(frozen=True)
class WorkMetrics:
    fanout_factor: float
    closure_ratio: float
    crystallization_debt: int
    generative_leverage: float
    validated_work_power: float
    evidence_per_compute_second: float
    queue_waste_ratio: float
    duplicate_work_ratio: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class ProofGates:
    coverage_preserved: bool
    required_checks_preserved: bool
    permissions_non_escalating: bool
    rollback_ready: bool
    evidence_comparable: bool

    @property
    def all_pass(self) -> bool:
        return all(asdict(self).values())
