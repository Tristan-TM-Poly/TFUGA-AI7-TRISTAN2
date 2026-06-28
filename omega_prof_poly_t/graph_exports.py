"""ProfessorGraph export helpers."""

from __future__ import annotations

from html import escape

from .json_exports import to_deterministic_json
from .professor_graph import ProfessorGraph


def professor_graph_to_json(graph: ProfessorGraph) -> str:
    return to_deterministic_json(
        {
            "nodes": [
                {
                    "id": node.node_id,
                    "kind": node.kind,
                    "label": node.label,
                    "metadata": node.metadata,
                }
                for node in sorted(graph.nodes.values(), key=lambda item: item.node_id)
            ],
            "edges": [
                {
                    "id": edge.edge_id,
                    "relation": edge.relation,
                    "node_ids": edge.node_ids,
                    "weight": edge.weight,
                }
                for edge in sorted(graph.edges.values(), key=lambda item: item.edge_id)
            ],
        }
    )


def professor_graph_to_graphml(graph: ProfessorGraph) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <graph id="ProfessorGraph" edgedefault="undirected">',
    ]
    for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
        lines.append(f'    <node id="{escape(node.node_id)}">')
        lines.append(f'      <data key="kind">{escape(node.kind)}</data>')
        lines.append(f'      <data key="label">{escape(node.label)}</data>')
        lines.append('    </node>')
    for edge in sorted(graph.edges.values(), key=lambda item: item.edge_id):
        if len(edge.node_ids) < 2:
            continue
        source = edge.node_ids[0]
        for target in edge.node_ids[1:]:
            edge_id = f"{edge.edge_id}:{source}:{target}"
            lines.append(f'    <edge id="{escape(edge_id)}" source="{escape(source)}" target="{escape(target)}">')
            lines.append(f'      <data key="relation">{escape(edge.relation)}</data>')
            lines.append(f'      <data key="weight">{edge.weight}</data>')
            lines.append('    </edge>')
    lines.extend(['  </graph>', '</graphml>', ''])
    return "\n".join(lines)
