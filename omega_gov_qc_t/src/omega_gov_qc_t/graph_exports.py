"""Graph export helpers for TristanGovGraph Quebec.

The module avoids heavy dependencies. It can emit adjacency dictionaries and a
small GraphML representation for demos, reviews and CI artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, Dict, List

from .gov_graph import GovGraph


@dataclass(frozen=True)
class GraphExportResult:
    """Graph export artifact."""

    name: str
    format: str
    content: str
    node_count: int
    edge_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "format": self.format,
            "content": self.content,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "oak_note": "Graph export is a structural representation, not an official public decision.",
        }


class GraphExporter:
    """Export GovGraph to dependency-free formats."""

    def adjacency_dict(self, graph: GovGraph) -> Dict[str, List[Dict[str, Any]]]:
        adjacency: Dict[str, List[Dict[str, Any]]] = {node_id: [] for node_id in graph.nodes}
        for edge in graph.edges:
            adjacency.setdefault(edge.source_id, []).append(
                {
                    "target_id": edge.target_id,
                    "relation": edge.relation,
                    "confidence": edge.confidence,
                    "evidence": edge.evidence,
                }
            )
        return adjacency

    def to_graphml(self, graph: GovGraph, *, name: str = "tristan_govgraph_qc") -> GraphExportResult:
        lines = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
            "  <key id=\"name\" for=\"node\" attr.name=\"name\" attr.type=\"string\"/>",
            "  <key id=\"type\" for=\"node\" attr.name=\"type\" attr.type=\"string\"/>",
            "  <key id=\"source\" for=\"node\" attr.name=\"source\" attr.type=\"string\"/>",
            "  <key id=\"relation\" for=\"edge\" attr.name=\"relation\" attr.type=\"string\"/>",
            "  <key id=\"confidence\" for=\"edge\" attr.name=\"confidence\" attr.type=\"double\"/>",
            f"  <graph id=\"{escape(name)}\" edgedefault=\"directed\">",
        ]

        for node in graph.nodes.values():
            lines.extend(
                [
                    f"    <node id=\"{escape(node.node_id)}\">",
                    f"      <data key=\"name\">{escape(node.name)}</data>",
                    f"      <data key=\"type\">{escape(node.node_type)}</data>",
                    f"      <data key=\"source\">{escape(node.source)}</data>",
                    "    </node>",
                ]
            )

        for index, edge in enumerate(graph.edges):
            edge_id = f"e{index}"
            lines.extend(
                [
                    f"    <edge id=\"{edge_id}\" source=\"{escape(edge.source_id)}\" target=\"{escape(edge.target_id)}\">",
                    f"      <data key=\"relation\">{escape(edge.relation)}</data>",
                    f"      <data key=\"confidence\">{edge.confidence:.6f}</data>",
                    "    </edge>",
                ]
            )

        lines.extend(["  </graph>", "</graphml>", ""])
        return GraphExportResult(
            name=name,
            format="graphml",
            content="\n".join(lines),
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
        )
