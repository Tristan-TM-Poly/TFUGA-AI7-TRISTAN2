"""Evidence primitives for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

EvidenceStatus = Literal["signal", "hypothesis", "structured_evidence", "reviewed", "decision_support"]


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim: str
    source_id: str
    asset_id: str = ""
    status: EvidenceStatus = "signal"
    confidence: float = 0.5
    method: str = "unknown"
    limitations: str = ""
    counter_explanations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.evidence_id.strip():
            errors.append("evidence_id is required")
        if not self.claim.strip():
            errors.append("claim is required")
        if not self.source_id.strip():
            errors.append("source_id is required")
        if self.status not in EvidenceStatus.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid evidence status: {self.status}")
        if not 0 <= self.confidence <= 1:
            errors.append("confidence must be between 0 and 1")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim": self.claim,
            "source_id": self.source_id,
            "asset_id": self.asset_id,
            "status": self.status,
            "confidence": self.confidence,
            "method": self.method,
            "limitations": self.limitations,
            "counter_explanations": list(self.counter_explanations),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class EvidenceGraph:
    def __init__(self) -> None:
        self.items: Dict[str, EvidenceItem] = {}
        self.m_minus: List[Dict[str, Any]] = []

    def add(self, item: EvidenceItem) -> None:
        errors = item.validate()
        if errors:
            raise ValueError("Invalid EvidenceItem: " + "; ".join(errors))
        if item.evidence_id in self.items:
            self.m_minus.append({"type": "duplicate_evidence", "evidence_id": item.evidence_id})
            raise ValueError(f"duplicate evidence_id: {item.evidence_id}")
        self.items[item.evidence_id] = item

    def for_asset(self, asset_id: str) -> List[EvidenceItem]:
        return [item for item in self.items.values() if item.asset_id == asset_id]

    def quality_report(self) -> Dict[str, Any]:
        status_counts: Dict[str, int] = {}
        for item in self.items.values():
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
        return {
            "evidence_count": len(self.items),
            "status_counts": status_counts,
            "m_minus_count": len(self.m_minus),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_infra_qc_t.evidence_graph.v0",
            "items": [item.to_dict() for item in self.items.values()],
            "quality": self.quality_report(),
            "m_minus": list(self.m_minus),
            "oak_note": "Evidence supports review; it is not a final authority decision.",
        }
