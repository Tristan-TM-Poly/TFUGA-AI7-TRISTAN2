from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping


_ALLOWED_STATUSES = {
    "IDEA",
    "FORMALIZED",
    "IMPLEMENTED",
    "TESTED",
    "BENCHMARKED",
    "SIMULATED",
    "MEASURED",
    "CERTIFIED_COMPUTATIONAL",
    "CERTIFIED_PHYSICS",
    "REFUTED",
    "ARCHIVED",
}


@dataclass(frozen=True)
class FluidGenome:
    """Canonical, serializable identity of one fluid-model cell.

    This is a data tensor/record, not a physical tensor. It is designed to make
    assumptions, units, evidence and failure boundaries explicit.
    """

    genome_id: str
    fluid_family: str
    regime: str
    phenomenon: str
    geometry: str
    boundary: str
    solver: str
    scale: str
    object_type: str
    uncertainty_class: str
    evidence_status: str = "IDEA"
    assumptions: tuple[str, ...] = ()
    quantities: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    epoch: int = 0
    local_index: int = 0

    def __post_init__(self) -> None:
        if not self.genome_id.strip():
            raise ValueError("genome_id must be non-empty")
        if self.evidence_status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported OAK status: {self.evidence_status}")
        if self.epoch < 0 or self.local_index < 0:
            raise ValueError("epoch and local_index must be non-negative")
        for key, unit in self.quantities.items():
            if not str(key).strip() or not str(unit).strip():
                raise ValueError("quantity names and units must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["assumptions"] = list(self.assumptions)
        payload["quantities"] = dict(self.quantities)
        payload["provenance"] = dict(self.provenance)
        return payload

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    def content_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()
