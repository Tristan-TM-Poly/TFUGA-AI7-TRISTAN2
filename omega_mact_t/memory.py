from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List


class MemoryDecision(str, Enum):
    KEEP = "KEEP"
    COMPRESS = "COMPRESS"
    REGENERATE_ON_DEMAND = "REGENERATE_ON_DEMAND"
    ARCHIVE = "ARCHIVE"
    HOLD_DELETE = "HOLD_DELETE"


@dataclass(frozen=True)
class MemoryObject:
    id: str
    storage_cost: float
    expected_recompute_cost: float
    causal_dependents: int = 0
    evidence_critical: bool = False
    provenance_critical: bool = False
    reconstructible: bool = False
    regeneration_verified: bool = False
    ttl_expired: bool = False


@dataclass(frozen=True)
class MemoryVerdict:
    object_id: str
    decision: MemoryDecision
    reason: str


def classify_memory(obj: MemoryObject) -> MemoryVerdict:
    if obj.evidence_critical or obj.provenance_critical:
        return MemoryVerdict(obj.id, MemoryDecision.KEEP, "evidence/provenance is non-disposable")
    if obj.causal_dependents > 0 and not obj.regeneration_verified:
        return MemoryVerdict(obj.id, MemoryDecision.KEEP, "downstream dependents and regeneration not verified")
    if obj.reconstructible and obj.regeneration_verified and obj.expected_recompute_cost <= obj.storage_cost:
        return MemoryVerdict(obj.id, MemoryDecision.REGENERATE_ON_DEMAND, "verified regeneration is cheaper than persistence")
    if obj.ttl_expired and obj.reconstructible:
        return MemoryVerdict(obj.id, MemoryDecision.ARCHIVE, "expired but reconstructible; archive before deletion review")
    if obj.reconstructible:
        return MemoryVerdict(obj.id, MemoryDecision.COMPRESS, "reconstructible but persistence can still be useful")
    return MemoryVerdict(obj.id, MemoryDecision.HOLD_DELETE, "not proven reconstructible; deletion not authorized")


def memory_portfolio(objects: Iterable[MemoryObject]) -> List[MemoryVerdict]:
    return [classify_memory(obj) for obj in objects]
