from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    path: str
    kind: str
    status: str
    sha256: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SummaryNode:
    id: str
    kind: str
    path: str
    title: str
    one_line: str
    status: str = "observed"
    tags: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceRef] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass(frozen=True)
class SummaryEdge:
    source: str
    target: str
    relation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class SummaryBundle:
    schema_version: str
    generated_at: str
    root: str
    depth: int
    audience: str
    focus: str | None
    nodes: list[SummaryNode]
    edges: list[SummaryEdge]
    health: dict[str, Any]
    gaps: list[dict[str, Any]]
    duplicate_candidates: list[dict[str, Any]]
    cache_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "root": self.root,
            "depth": self.depth,
            "audience": self.audience,
            "focus": self.focus,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "health": self.health,
            "gaps": self.gaps,
            "duplicate_candidates": self.duplicate_candidates,
            "cache_fingerprint": self.cache_fingerprint,
        }
