"""Dependency-free graph exports for InfrastructureGraph Quebec."""

from __future__ import annotations

from html import escape
from typing import List

from .infra_graph import InfraGraph


class GraphMLExporter:
    """Export a public-safe GraphML representation.

    This exporter intentionally emits only public-safe summaries when requested.
    Sensitive labels, notes and metadata are redacted through AssetNode/DependencyEdge
    public-safe serialization.
    """

    def export(self, graph: InfraGraph, *, public_safe: bool = True) -> str:
        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <key id="sector" for="node" attr.name="sector" attr.type="string"/>',
            '  <key id="owner_type" for="node" attr.name="owner_type" attr.type="string"/>',
            '  <key id="visibility" for="node" attr.name="visibility" attr.type="string"/>',
            '  <key id="criticality" for="node" attr.name="criticality" attr.type="int"/>',
            '  <key id="kind" for="edge" attr.name="kind" attr.type="string"/>',
            '  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>',
            '  <graph id="InfrastructureGraphQuebec" edgedefault="directed">',
        ]

        for asset in graph.assets.values():
            payload = asset.to_dict(public_safe=public_safe)
            node_id = escape(payload["asset_id"])
            lines.extend(
                [
                    f'    <node id="{node_id}">',
                    f'      <data key="label">{escape(str(payload["name"]))}</data>',
                    f'      <data key="sector">{escape(str(payload["sector"]))}</data>',
                    f'      <data key="owner_type">{escape(str(payload["owner_type"]))}</data>',
                    f'      <data key="visibility">{escape(str(payload["visibility"]))}</data>',
                    f'      <data key="criticality">{int(payload["criticality"])}</data>',
                    '    </node>',
                ]
            )

        for idx, edge in enumerate(graph.dependencies):
            payload = edge.to_dict(public_safe=public_safe)
            edge_id = f"edge:{idx}"
            lines.extend(
                [
                    f'    <edge id="{escape(edge_id)}" source="{escape(payload["source_asset_id"])}" target="{escape(payload["target_asset_id"])}">',
                    f'      <data key="kind">{escape(str(payload["kind"]))}</data>',
                    f'      <data key="confidence">{float(payload["confidence"])}</data>',
                    '    </edge>',
                ]
            )

        lines.extend(['  </graph>', '</graphml>', ''])
        return "\n".join(lines)
