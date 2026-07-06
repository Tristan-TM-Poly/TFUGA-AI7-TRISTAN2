"""Core graph primitives for Ω-GOV-QC-T.

This file intentionally avoids network calls and external dependencies. It is a
small, auditable nucleus that can later be connected to Données Québec,
municipal open data portals, procurement datasets, and dashboards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional

GovNodeType = Literal[
    "ministry",
    "organization",
    "municipality",
    "mrc",
    "region",
    "program",
    "contract",
    "dataset",
    "indicator",
    "risk",
    "service",
    "law",
    "report",
]

OAKStatus = Literal["A", "B", "C", "D", "M-", "blocked"]


@dataclass(frozen=True)
class GovNode:
    """A government graph node with provenance and OAK metadata."""

    node_id: str
    name: str
    node_type: GovNodeType
    source: str
    oak_status: OAKStatus = "B"
    jurisdiction: str = "Québec"
    description: str = ""
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.node_id.strip():
            errors.append("node_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.source.strip():
            errors.append("source/provenance is required")
        if self.node_type not in GovNodeType.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid node_type: {self.node_type}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type,
            "source": self.source,
            "oak_status": self.oak_status,
            "jurisdiction": self.jurisdiction,
            "description": self.description,
            "retrieved_at": self.retrieved_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GovEdge:
    """Directed relation between two government nodes."""

    source_id: str
    target_id: str
    relation: str
    evidence: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.source_id.strip():
            errors.append("source_id is required")
        if not self.target_id.strip():
            errors.append("target_id is required")
        if not self.relation.strip():
            errors.append("relation is required")
        if not self.evidence.strip():
            errors.append("evidence is required")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append("confidence must be between 0 and 1")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


@dataclass
class GovGraph:
    """Minimal in-memory graph for ministries, organizations and public data."""

    nodes: Dict[str, GovNode] = field(default_factory=dict)
    edges: List[GovEdge] = field(default_factory=list)
    m_minus: List[str] = field(default_factory=list)

    def add_node(self, node: GovNode) -> None:
        errors = node.validate()
        if errors:
            raise ValueError("Invalid GovNode: " + "; ".join(errors))
        if node.node_id in self.nodes:
            self.m_minus.append(f"duplicate node ignored: {node.node_id}")
            raise ValueError(f"duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GovEdge) -> None:
        errors = edge.validate()
        if errors:
            raise ValueError("Invalid GovEdge: " + "; ".join(errors))
        missing = [n for n in (edge.source_id, edge.target_id) if n not in self.nodes]
        if missing:
            self.m_minus.append(f"edge references missing nodes: {missing}")
            raise ValueError(f"edge references missing nodes: {missing}")
        self.edges.append(edge)

    def isolated_nodes(self) -> List[str]:
        connected = {edge.source_id for edge in self.edges} | {edge.target_id for edge in self.edges}
        return [node_id for node_id in self.nodes if node_id not in connected]

    def nodes_by_type(self, node_type: GovNodeType) -> List[GovNode]:
        return [node for node in self.nodes.values() if node.node_type == node_type]

    def quality_report(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for node in self.nodes.values():
            by_type[node.node_type] = by_type.get(node.node_type, 0) + 1

        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": by_type,
            "isolated_nodes": self.isolated_nodes(),
            "m_minus": list(self.m_minus),
            "oak_note": "Graph quality report only; not a public decision or verdict.",
        }

    def export_json_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.gov_graph.v0",
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "quality_report": self.quality_report(),
        }

    @classmethod
    def from_nodes_edges(
        cls,
        nodes: Iterable[GovNode],
        edges: Optional[Iterable[GovEdge]] = None,
    ) -> "GovGraph":
        graph = cls()
        for node in nodes:
            graph.add_node(node)
        for edge in edges or []:
            graph.add_edge(edge)
        return graph
