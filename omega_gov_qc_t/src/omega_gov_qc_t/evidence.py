"""Evidence primitives for Ω-GOV-QC-T.

Evidence records connect a claim to a source and keep uncertainty visible. The
module is intentionally conservative: evidence items support analysis and
review, not final public authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

EvidenceStatus = Literal["signal", "hypothesis", "structured_evidence", "recommendation", "human_decision"]


@dataclass(frozen=True)
class EvidenceItem:
    """A traceable evidence item for a claim or report section."""

    evidence_id: str
    claim: str
    source_id: str
    status: EvidenceStatus = "signal"
    confidence: float = 0.5
    method: str = "documented_observation"
    limitations: str = ""
    counter_explanations: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.evidence_id.strip():
            errors.append("evidence_id is required")
        if not self.claim.strip():
            errors.append("claim is required")
        if not self.source_id.strip():
            errors.append("source_id is required")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append("confidence must be between 0 and 1")
        if self.status == "human_decision":
            errors.append("human_decision should be recorded outside automated evidence generation")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim": self.claim,
            "source_id": self.source_id,
            "status": self.status,
            "confidence": self.confidence,
            "method": self.method,
            "limitations": self.limitations,
            "counter_explanations": list(self.counter_explanations),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class EvidenceGraph:
    """Minimal claim-source graph."""

    items: Dict[str, EvidenceItem] = field(default_factory=dict)
    by_source: Dict[str, List[str]] = field(default_factory=dict)
    m_minus: List[str] = field(default_factory=list)

    def add(self, item: EvidenceItem) -> None:
        errors = item.validate()
        if errors:
            raise ValueError("Invalid EvidenceItem: " + "; ".join(errors))
        if item.evidence_id in self.items:
            self.m_minus.append(f"duplicate evidence ignored: {item.evidence_id}")
            raise ValueError(f"duplicate evidence_id: {item.evidence_id}")
        self.items[item.evidence_id] = item
        self.by_source.setdefault(item.source_id, []).append(item.evidence_id)

    def items_for_source(self, source_id: str) -> List[EvidenceItem]:
        return [self.items[item_id] for item_id in self.by_source.get(source_id, [])]

    def quality_report(self) -> Dict[str, Any]:
        low_confidence = [
            item.evidence_id for item in self.items.values() if item.confidence < 0.5
        ]
        missing_limits = [
            item.evidence_id for item in self.items.values() if not item.limitations.strip()
        ]
        return {
            "evidence_count": len(self.items),
            "low_confidence": low_confidence,
            "missing_limitations": missing_limits,
            "m_minus": list(self.m_minus),
            "oak_note": "Evidence supports review and explanation; it is not final authority.",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.evidence_graph.v0",
            "items": [item.to_dict() for item in self.items.values()],
            "quality_report": self.quality_report(),
        }
