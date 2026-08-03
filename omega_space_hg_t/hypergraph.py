"""Evidence-bearing hypergraph primitives for Ω-SPACE-HG-T∞."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable


@dataclass(frozen=True)
class SpaceNode:
    node_id: str
    kind: str
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    oak_status: str = "model"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True)
class SpaceHyperedge:
    edge_id: str
    relation: str
    members: tuple[str, ...]
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["members"] = list(self.members)
        payload["evidence"] = list(self.evidence)
        return payload


class SpaceHypergraph:
    """Small deterministic hypergraph with validation and content digest."""

    def __init__(self, graph_id: str) -> None:
        self.graph_id = graph_id
        self._nodes: dict[str, SpaceNode] = {}
        self._edges: dict[str, SpaceHyperedge] = {}

    @property
    def nodes(self) -> tuple[SpaceNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[SpaceHyperedge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def add_node(self, node: SpaceNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate node: {node.node_id}")
        self._nodes[node.node_id] = node

    def add_edge(self, edge: SpaceHyperedge) -> None:
        if edge.edge_id in self._edges:
            raise ValueError(f"duplicate edge: {edge.edge_id}")
        if len(edge.members) < 2:
            raise ValueError("a hyperedge must connect at least two members")
        missing = [member for member in edge.members if member not in self._nodes]
        if missing:
            raise ValueError(f"unknown hyperedge members: {missing}")
        self._edges[edge.edge_id] = edge

    def neighbors(self, node_id: str) -> tuple[str, ...]:
        if node_id not in self._nodes:
            raise KeyError(node_id)
        result: set[str] = set()
        for edge in self._edges.values():
            if node_id in edge.members:
                result.update(member for member in edge.members if member != node_id)
        return tuple(sorted(result))

    def critical_singletons(self) -> tuple[str, ...]:
        """Return functional nodes with no same-kind alternative.

        This is a deliberately conservative structural indicator, not a full
        reliability or fault-tree analysis.
        """

        counts: dict[str, int] = {}
        for node in self._nodes.values():
            counts[node.kind] = counts.get(node.kind, 0) + 1
        return tuple(
            sorted(
                node.node_id
                for node in self._nodes.values()
                if counts[node.kind] == 1 and node.kind not in {"mission", "requirement", "evidence"}
            )
        )

    def validate(self) -> dict[str, Any]:
        orphan_nodes = sorted(
            node_id
            for node_id in self._nodes
            if not any(node_id in edge.members for edge in self._edges.values())
        )
        return {
            "valid": not orphan_nodes and bool(self._nodes) and bool(self._edges),
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "orphan_nodes": orphan_nodes,
            "critical_singletons": list(self.critical_singletons()),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "graph_id": self.graph_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "hyperedges": [edge.to_dict() for edge in self.edges],
            "validation": self.validate(),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def build_spacecraft_hypergraph(
    mission_id: str,
    subsystem_names: Iterable[str],
    requirements: Iterable[str] = (),
) -> SpaceHypergraph:
    graph = SpaceHypergraph(graph_id=f"space:{mission_id}")
    graph.add_node(SpaceNode(mission_id, "mission", {"mission_id": mission_id}, oak_status="declared"))
    subsystem_ids: list[str] = []
    for name in subsystem_names:
        node_id = f"subsystem:{name}"
        subsystem_ids.append(node_id)
        graph.add_node(SpaceNode(node_id, name, {"name": name}, oak_status="model"))
        graph.add_edge(SpaceHyperedge(f"contains:{name}", "contains", (mission_id, node_id)))
    for index, statement in enumerate(requirements):
        node_id = f"requirement:{index:03d}"
        graph.add_node(SpaceNode(node_id, "requirement", {"statement": statement}, oak_status="unverified"))
        graph.add_edge(
            SpaceHyperedge(
                f"traces:{index:03d}",
                "traces_to",
                tuple([node_id, mission_id, *subsystem_ids]),
            )
        )
    return graph
