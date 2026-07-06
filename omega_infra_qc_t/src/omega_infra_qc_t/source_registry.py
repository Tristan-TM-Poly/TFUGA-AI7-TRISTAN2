"""Source registry for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal

SourceKind = Literal["open_data", "public_report", "manual_note", "authorized_private", "demo"]
Permission = Literal["allowed", "review_required", "blocked"]


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    kind: SourceKind = "demo"
    locator: str = ""
    permission: Permission = "review_required"
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.source_id.strip():
            errors.append("source_id is required")
        if not self.title.strip():
            errors.append("title is required")
        if self.kind not in SourceKind.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid source kind: {self.kind}")
        if self.permission not in Permission.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid permission: {self.permission}")
        return errors

    @property
    def fingerprint(self) -> str:
        payload = f"{self.source_id}|{self.title}|{self.kind}|{self.locator}|{self.retrieved_at}"
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


class SourceRegistry:
    def __init__(self) -> None:
        self.sources: Dict[str, SourceRecord] = {}
        self.m_minus: List[Dict[str, Any]] = []

    def add(self, source: SourceRecord) -> None:
        errors = source.validate()
        if errors:
            raise ValueError("Invalid SourceRecord: " + "; ".join(errors))
        if source.source_id in self.sources:
            self.m_minus.append({"type": "duplicate_source", "source_id": source.source_id})
            raise ValueError(f"duplicate source_id: {source.source_id}")
        self.sources[source.source_id] = source

    def quality_report(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.sources),
            "allowed": [s.source_id for s in self.sources.values() if s.permission == "allowed"],
            "review_required": [s.source_id for s in self.sources.values() if s.permission == "review_required"],
            "blocked": [s.source_id for s in self.sources.values() if s.permission == "blocked"],
            "m_minus_count": len(self.m_minus),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_infra_qc_t.source_registry.v0",
            "sources": [source.to_dict() for source in self.sources.values()],
            "quality": self.quality_report(),
            "m_minus": list(self.m_minus),
        }
