"""Enriched ProfessorGraph export helpers for Omega absorb v0.7."""

from __future__ import annotations

from html import escape

from .professor_graph import ProfessorGraph


def professor_graph_to_enriched_graphml(graph: ProfessorGraph) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="source" for="node" attr.name="source" attr.type="string"/>',
        '  <key id="link" for="node" attr.name="link" attr.type="string"/>',
        '  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '  <graph id="ProfessorGraphPoly" edgedefault="undirected">',
    ]
    for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
        lines.append(f'    <node id="{escape(node.node_id)}">')
        lines.append(f'      <data key="kind">{escape(node.kind)}</data>')
        lines.append(f'      <data key="label">{escape(node.label)}</data>')
        source = node.metadata.get("source", "")
        link = node.metadata.get("link", "")
        if source:
            lines.append(f'      <data key="source">{escape(source)}</data>')
        if link:
            lines.append(f'      <data key="link">{escape(link)}</data>')
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
