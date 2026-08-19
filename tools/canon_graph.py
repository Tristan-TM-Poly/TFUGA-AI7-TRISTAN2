"""CanonGraph primitives for Tristan CanonOS.

A lightweight in-memory graph for canonical objects and relations. It is designed
for planning, audit, and tests; it does not mutate external systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class CanonNodeType(StrEnum):
    IDEA = "idea"
    THEORY = "theory"
    FILE = "file"
    TOOL = "tool"
    TEST = "test"
    PROOF = "proof"
    ERROR = "error"
    PROTOTYPE = "prototype"
    PULL_REQUEST = "pull_request"
    RISK = "risk"
    SOURCE = "source"
    MEASUREMENT = "measurement"
    RESIDUE = "residue"
    ROADMAP = "roadmap"


class CanonRelation(StrEnum):
    INSPIRES = "inspires"
    PROVES = "proves"
    CONTRADICTS = "contradicts"
    IMPROVES = "improves"
    REPLACES = "replaces"
    INVALIDATES = "invalidates"
    DEPENDS_ON = "depends_on"
    TESTS = "tests"
    FALSIFIES = "falsifies"
    IMPLEMENTS = "implements"
    DOCUMENTS = "documents"
    WARNS_ABOUT = "warns_about"
    MEASURES = "measures"
    QUARANTINES = "quarantines"


@dataclass(frozen=True)
class CanonNode:
    node_id: str
    title: str
    node_type: CanonNodeType
    reality_level: str = "R1_VISION"
    proof_level: str = "P0_NO_EVIDENCE"
    canon_rank: str = "C1_CAPTURED_IDEA"
    paths: tuple[str, ...] = ()
    oak_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: CanonRelation
    confidence: float = 0.5
    oak_notes: tuple[str, ...] = ()


@dataclass
class CanonGraph:
    nodes: dict[str, CanonNode] = field(default_factory=dict)
    edges: dict[str, CanonEdge] = field(default_factory=dict)

    def add_node(self, node: CanonNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate canon node: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: CanonEdge) -> None:
        if edge.edge_id in self.edges:
            raise ValueError(f"duplicate canon edge: {edge.edge_id}")
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("edge endpoints must exist before linking")
        if not 0 <= edge.confidence <= 1:
            raise ValueError("edge confidence must be in [0, 1]")
        self.edges[edge.edge_id] = edge

    def neighbors(self, node_id: str) -> tuple[CanonNode, ...]:
        ids = [edge.target_id for edge in self.edges.values() if edge.source_id == node_id]
        return tuple(self.nodes[target_id] for target_id in ids)

    def orphan_nodes(self) -> tuple[CanonNode, ...]:
        linked = {edge.source_id for edge in self.edges.values()} | {edge.target_id for edge in self.edges.values()}
        return tuple(node for node_id, node in self.nodes.items() if node_id not in linked)

    def contradiction_edges(self) -> tuple[CanonEdge, ...]:
        return tuple(edge for edge in self.edges.values() if edge.relation == CanonRelation.CONTRADICTS)
