from __future__ import annotations

from html import escape
from typing import Any, Iterable

from .models import GraphEdge, GraphNode


class EvidenceHypergraph:
    """Traceability graph linking intent, requirements, work, artifacts and evidence."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def add_node(self, node: GraphNode) -> None:
        existing = self._nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"conflicting node id: {node.node_id}")
        self._nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self._edges[edge.edge_id] = edge

    def extend(self, *, nodes: Iterable[GraphNode] = (), edges: Iterable[GraphEdge] = ()) -> None:
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for edge in self.edges:
            if edge.source not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing source {edge.source}")
            if edge.target not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing target {edge.target}")
        return tuple(errors)

    def incoming(self, node_id: str, relation: str | None = None) -> tuple[GraphEdge, ...]:
        return tuple(
            edge for edge in self.edges
            if edge.target == node_id and (relation is None or edge.relation == relation)
        )

    def outgoing(self, node_id: str, relation: str | None = None) -> tuple[GraphEdge, ...]:
        return tuple(
            edge for edge in self.edges
            if edge.source == node_id and (relation is None or edge.relation == relation)
        )

    def to_dict(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for node in self.nodes:
            by_type[node.node_type] = by_type.get(node.node_type, 0) + 1
        return {
            "schema": "omega-intent-hypergraph/v1",
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "summary": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "node_types": dict(sorted(by_type.items())),
                "validation_errors": list(self.validate()),
            },
        }

    def to_graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="type" for="node" attr.name="type" attr.type="string"/>',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
            '  <graph id="omega-intent" edgedefault="directed">',
        ]
        for node in self.nodes:
            lines.extend([
                f'    <node id="{escape(node.node_id)}">',
                f'      <data key="type">{escape(node.node_type)}</data>',
                f'      <data key="label">{escape(node.label)}</data>',
                '    </node>',
            ])
        for edge in self.edges:
            lines.extend([
                f'    <edge id="{escape(edge.edge_id)}" source="{escape(edge.source)}" target="{escape(edge.target)}">',
                f'      <data key="relation">{escape(edge.relation)}</data>',
                '    </edge>',
            ])
        lines.extend(['  </graph>', '</graphml>', ''])
        return "\n".join(lines)
