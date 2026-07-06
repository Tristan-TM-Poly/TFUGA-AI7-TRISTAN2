"""Source registry primitives for Ω-GOV-QC-T.

The registry is a small provenance layer. It does not fetch remote data. It
records what a source is, when it was registered, what use is allowed, and a
stable fingerprint for audit trails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal

SourceKind = Literal["open_data", "official_page", "report", "api", "manual_note", "example"]
UsePermission = Literal["allowed", "review_required", "blocked"]


@dataclass(frozen=True)
class SourceRecord:
    """A traceable source record."""

    source_id: str
    title: str
    kind: SourceKind
    locator: str
    permission: UsePermission = "review_required"
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.source_id.strip():
            errors.append("source_id is required")
        if not self.title.strip():
            errors.append("title is required")
        if not self.locator.strip():
            errors.append("locator is required")
        return errors

    @property
    def fingerprint(self) -> str:
        payload = "|".join(
            [
                self.source_id,
                self.title,
                self.kind,
                self.locator,
                self.permission,
                self.retrieved_at,
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "kind": self.kind,
            "locator": self.locator,
            "permission": self.permission,
            "retrieved_at": self.retrieved_at,
            "fingerprint": self.fingerprint,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


@dataclass
class SourceRegistry:
    """In-memory registry for source provenance."""

    sources: Dict[str, SourceRecord] = field(default_factory=dict)
    m_minus: List[str] = field(default_factory=list)

    def add(self, source: SourceRecord) -> None:
        errors = source.validate()
        if errors:
            raise ValueError("Invalid SourceRecord: " + "; ".join(errors))
        if source.source_id in self.sources:
            self.m_minus.append(f"duplicate source ignored: {source.source_id}")
            raise ValueError(f"duplicate source_id: {source.source_id}")
        self.sources[source.source_id] = source

    def allowed_sources(self) -> List[SourceRecord]:
        return [source for source in self.sources.values() if source.permission == "allowed"]

    def blocked_sources(self) -> List[SourceRecord]:
        return [source for source in self.sources.values() if source.permission == "blocked"]

    def review_required_sources(self) -> List[SourceRecord]:
        return [source for source in self.sources.values() if source.permission == "review_required"]

    def quality_report(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.sources),
            "allowed_count": len(self.allowed_sources()),
            "review_required_count": len(self.review_required_sources()),
            "blocked_count": len(self.blocked_sources()),
            "m_minus": list(self.m_minus),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.source_registry.v0",
            "sources": [source.to_dict() for source in self.sources.values()],
            "quality_report": self.quality_report(),
        }
