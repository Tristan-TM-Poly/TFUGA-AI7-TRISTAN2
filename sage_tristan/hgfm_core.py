"""Minimal HGFM core for Omega Math Tristan.

HGFM = HyperGraphe Fractal Mycelien: a typed directed hypergraph connecting
claims, definitions, proofs, prototypes, residues, tests and memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

EdgeType = Literal[
    "defines",
    "proves",
    "tests",
    "refutes",
    "generalizes",
    "compresses",
    "expands",
    "depends_on",
    "blocks",
    "promotes",
]


@dataclass(frozen=True)
class HGFMNodeState:
    """Bayes/OAK-like state attached to an HGFM node."""

    confidence: float = 0.0
    utility: float = 0.0
    fertility: float = 0.0
    testability: float = 0.0
    compressibility: float = 0.0
    risk: float = 0.0
    oak_maturity: float = 0.0

    def bounded(self) -> "HGFMNodeState":
        def c(x: float) -> float:
            return max(0.0, min(1.0, float(x)))

        return HGFMNodeState(
            confidence=c(self.confidence),
            utility=c(self.utility),
            fertility=c(self.fertility),
            testability=c(self.testability),
            compressibility=c(self.compressibility),
            risk=c(self.risk),
            oak_maturity=c(self.oak_maturity),
        )

    def action_energy(self) -> float:
        """Return a compact action-energy score."""
        s = self.bounded()
        return (
            s.confidence
            + s.utility
            + s.fertility
            + s.testability
            + s.compressibility
            + s.oak_maturity
            - s.risk
        ) / 6.0


@dataclass(frozen=True)
class HGFMNode:
    id: str
    label: str
    kind: str
    layer: str = "math"
    scale: str = "meso"
    state: HGFMNodeState = field(default_factory=HGFMNodeState)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HGFMHyperEdge:
    id: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    edge_type: EdgeType
    weight: float = 1.0
    oak_status: str = "OAK-0"
    residue: tuple[str, ...] = ()

    def touches(self, node_id: str) -> bool:
        return node_id in self.sources or node_id in self.targets


@dataclass
class HGFMGraph:
    """Small dependency-free directed hypergraph."""

    nodes: dict[str, HGFMNode] = field(default_factory=dict)
    edges: dict[str, HGFMHyperEdge] = field(default_factory=dict)

    def add_node(self, node: HGFMNode) -> None:
        if node.id in self.nodes:
            raise ValueError(f"node already exists: {node.id}")
        self.nodes[node.id] = node

    def add_edge(self, edge: HGFMHyperEdge) -> None:
        if edge.id in self.edges:
            raise ValueError(f"edge already exists: {edge.id}")
        missing = [node for node in (*edge.sources, *edge.targets) if node not in self.nodes]
        if missing:
            raise ValueError(f"edge references missing nodes: {missing}")
        self.edges[edge.id] = edge

    def incoming(self, node_id: str) -> list[HGFMHyperEdge]:
        return [edge for edge in self.edges.values() if node_id in edge.targets]

    def outgoing(self, node_id: str) -> list[HGFMHyperEdge]:
        return [edge for edge in self.edges.values() if node_id in edge.sources]

    def neighbors(self, node_id: str) -> set[str]:
        linked: set[str] = set()
        for edge in self.edges.values():
            if edge.touches(node_id):
                linked.update(edge.sources)
                linked.update(edge.targets)
        linked.discard(node_id)
        return linked

    def centrality_proxy(self) -> dict[str, int]:
        """Return a lightweight degree-like centrality proxy."""
        return {node_id: len(self.incoming(node_id)) + len(self.outgoing(node_id)) for node_id in self.nodes}

    def fertility_density(self, *, negative_motifs: int = 0) -> float:
        """Return a simple fertility density for graph governance."""
        validated_outputs = sum(1 for node in self.nodes.values() if node.state.oak_maturity >= 0.5)
        denominator = 1 + len(self.nodes) + len(self.edges) + max(0, negative_motifs)
        return validated_outputs / denominator

    def blocked_edges(self) -> list[HGFMHyperEdge]:
        return [edge for edge in self.edges.values() if edge.edge_type == "blocks" or edge.oak_status in {"OAK-R", "refuted"}]


def build_claim_test_graph(claim_id: str, test_id: str, result_id: str, *, passed: bool) -> HGFMGraph:
    """Create a tiny claim -> test -> result HGFM graph."""
    graph = HGFMGraph()
    graph.add_node(HGFMNode(id=claim_id, label="claim", kind="claim", state=HGFMNodeState(fertility=0.7, testability=0.8, oak_maturity=0.2)))
    graph.add_node(HGFMNode(id=test_id, label="test", kind="test", state=HGFMNodeState(testability=1.0, oak_maturity=0.3)))
    graph.add_node(HGFMNode(id=result_id, label="result", kind="result", state=HGFMNodeState(confidence=0.7 if passed else 0.2, oak_maturity=0.5 if passed else 0.1, risk=0.1 if passed else 0.8)))
    graph.add_edge(HGFMHyperEdge(id=f"{claim_id}->{test_id}", sources=(claim_id,), targets=(test_id,), edge_type="tests", oak_status="OAK-3"))
    graph.add_edge(HGFMHyperEdge(id=f"{test_id}->{result_id}", sources=(test_id,), targets=(result_id,), edge_type="promotes" if passed else "refutes", oak_status="OAK-5" if passed else "OAK-2"))
    return graph
