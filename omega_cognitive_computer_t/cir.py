from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return sorted((_json_safe(v) for v in value), key=lambda x: repr(x))
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dataclass_fields__"):
        return _json_safe(asdict(value))
    return {"__repr__": repr(value), "__type__": type(value).__name__}


@dataclass(frozen=True)
class EvidenceItem:
    claim: str
    source: str = ""
    strength: float = 0.0
    kind: str = "observation"
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Evidence strength must be in [0, 1]")


@dataclass
class CognitiveState:
    """Ω-CIR-T: domain-neutral intermediate representation for a reasoning state."""

    objects: dict[str, Any] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)
    uncertainty: dict[str, float] = field(default_factory=dict)
    representations: dict[str, Any] = field(default_factory=dict)
    provenance: list[str] = field(default_factory=list)
    scale: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def clone(self) -> "CognitiveState":
        return deepcopy(self)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def fingerprint(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def add_evidence(self, item: EvidenceItem) -> None:
        self.evidence.append(item)

    def deduplicate(self) -> None:
        self.goals = _stable_unique(self.goals)
        self.hypotheses = _stable_unique(self.hypotheses)
        self.assumptions = _stable_unique(self.assumptions)
        self.constraints = _stable_unique(self.constraints)
        self.provenance = _stable_unique(self.provenance)
        seen: set[str] = set()
        unique_evidence: list[EvidenceItem] = []
        for item in self.evidence:
            key = json.dumps(_json_safe(asdict(item)), sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                unique_evidence.append(item)
        self.evidence = unique_evidence


def _stable_unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
