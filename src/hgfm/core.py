"""Core data structures for Tristan Hypergraphs / HGFM.

The goal of this first implementation is intentionally modest:
- typed nodes;
- typed multi-input/multi-output hyperedges;
- OAK/Omegagate statuses;
- Omega scoring;
- negative memory M-;
- primitive CVCD candidate extraction.

This is a seed engine, not yet the full HGFMnD∞ formal system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal
import uuid


OakStatus = Literal[
    "TRACE",
    "COHERENT",
    "FERTILE",
    "TESTABLE",
    "TESTED",
    "REPRODUCED",
    "MEASURED",
    "PROVEN",
    "CANON",
    "M_MINUS",
]

OmegaGate = Literal["NEG", "P0", "ACTIVE", "UNKNOWN", "CERTIFIED"]


@dataclass
class HGFMNode:
    """A typed node in a Tristan Hypergraph."""

    id: str
    type: str
    content: Any
    layer: str
    scale: str
    oak_status: OakStatus = "TRACE"
    omegagate: OmegaGate = "UNKNOWN"
    evidence: List[str] = field(default_factory=list)
    residue: List[str] = field(default_factory=list)
    memory_refs: List[str] = field(default_factory=list)
    next_tests: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class HGFMEdge:
    """A typed multi-input/multi-output transformation."""

    id: str
    type: str
    inputs: List[str]
    outputs: List[str]
    transform: str
    constraints: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    residue: List[str] = field(default_factory=list)
    oak_status: OakStatus = "TRACE"
    omegagate: OmegaGate = "UNKNOWN"
    scores: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.inputs:
            raise ValueError("HGFMEdge requires at least one input node id")
        if not self.outputs:
            raise ValueError("HGFMEdge requires at least one output node id")


@dataclass
class HGFM:
    """Minimal in-memory Tristan Hypergraph."""

    nodes: Dict[str, HGFMNode] = field(default_factory=dict)
    edges: Dict[str, HGFMEdge] = field(default_factory=dict)
    m_plus: List[str] = field(default_factory=list)
    m_minus: List[str] = field(default_factory=list)

    def add_node(self, **kwargs: Any) -> str:
        node_id = kwargs.get("id") or f"node_{uuid.uuid4().hex[:8]}"
        kwargs["id"] = node_id
        self.nodes[node_id] = HGFMNode(**kwargs)
        return node_id

    def add_edge(self, **kwargs: Any) -> str:
        edge_id = kwargs.get("id") or f"edge_{uuid.uuid4().hex[:8]}"
        kwargs["id"] = edge_id
        edge = HGFMEdge(**kwargs)

        missing_inputs = [node_id for node_id in edge.inputs if node_id not in self.nodes]
        missing_outputs = [node_id for node_id in edge.outputs if node_id not in self.nodes]
        if missing_inputs or missing_outputs:
            raise KeyError(
                "edge references missing nodes: "
                f"inputs={missing_inputs}, outputs={missing_outputs}"
            )

        self.edges[edge_id] = edge
        return edge_id

    def omega_score(self, node_id: str) -> float:
        """Compute a conservative Omega score for a node.

        Positive terms: logic, fertility, validation, utility, value, recognition.
        Negative terms: residue, risk, cost, hallucination.
        """

        node = self.nodes[node_id]
        s = node.scores
        return (
            1.0 * s.get("logic", 0.0)
            + 1.2 * s.get("fertility", 0.0)
            + 1.5 * s.get("validation", 0.0)
            + 1.1 * s.get("utility", 0.0)
            + 1.0 * s.get("value", 0.0)
            + 0.8 * s.get("recognition", 0.0)
            - 1.3 * s.get("residue", 0.0)
            - 1.2 * s.get("risk", 0.0)
            - 0.8 * s.get("cost", 0.0)
            - 2.0 * s.get("hallucination", 0.0)
        )

    def oak_gate(self, node_id: str) -> OmegaGate:
        """Map OAK status and Omega score to an Omegagate decision."""

        node = self.nodes[node_id]
        score = self.omega_score(node_id)

        if node.oak_status == "M_MINUS":
            return "NEG"
        if node.oak_status in {"MEASURED", "PROVEN", "CANON"}:
            return "CERTIFIED"
        if score >= 4.0 and node.oak_status in {"FERTILE", "TESTABLE", "TESTED", "REPRODUCED"}:
            return "ACTIVE"
        if score >= 2.0:
            return "P0"
        return "UNKNOWN"

    def update_omegagates(self) -> None:
        """Refresh all node Omegagate decisions."""

        for node_id, node in self.nodes.items():
            node.omegagate = self.oak_gate(node_id)

    def register_failure(self, item_id: str, reason: str, guardrail: str | None = None) -> None:
        """Write a failure into M- and mark the item as negative memory.

        M- is not deletion. It is a reusable immune-system record.
        """

        entry = reason if guardrail is None else f"{reason} | guardrail: {guardrail}"
        self.m_minus.append(f"{item_id}: {entry}")

        if item_id in self.nodes:
            node = self.nodes[item_id]
            node.oak_status = "M_MINUS"
            node.omegagate = "NEG"
            node.residue.append(reason)
            if guardrail:
                node.next_tests.append(guardrail)

    def cvcd_candidates(self) -> List[HGFMNode]:
        """Return nodes whose scores suggest compressed fertile invariants.

        This is a heuristic placeholder for the future CVCD engine.
        """

        candidates: List[HGFMNode] = []
        for node in self.nodes.values():
            fertility = node.scores.get("fertility", 0.0)
            compression = node.scores.get("compression", 0.0)
            stability = node.scores.get("stability", 0.0)
            residue = node.scores.get("residue", 0.0)
            risk = node.scores.get("risk", 0.0)
            if fertility + compression + stability - residue - risk > 1.5:
                candidates.append(node)
        return candidates

    def incidence(self) -> Dict[str, Dict[str, int]]:
        """Return a simple node-edge incidence map.

        Values:
        - -1 for input;
        - +1 for output;
        - 0 omitted.
        """

        result: Dict[str, Dict[str, int]] = {node_id: {} for node_id in self.nodes}
        for edge_id, edge in self.edges.items():
            for node_id in edge.inputs:
                result[node_id][edge_id] = -1
            for node_id in edge.outputs:
                result[node_id][edge_id] = 1
        return result
