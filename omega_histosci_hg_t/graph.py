"""Deterministic directed hypergraph engine for historical science records."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from html import escape
from typing import Iterable, Iterator

from .models import (
    EdgeKind,
    HistoricalHyperedge,
    HistoricalNode,
    NodeKind,
    TemporalLayer,
    content_hash,
)


@dataclass(frozen=True, slots=True)
class GraphAudit:
    valid: bool
    node_count: int
    edge_count: int
    dangling_node_ids: tuple[str, ...]
    duplicate_edge_signatures: tuple[str, ...]
    orphan_node_ids: tuple[str, ...]
    digest: str


class HistoricalHypergraph:
    def __init__(self) -> None:
        self._nodes: dict[str, HistoricalNode] = {}
        self._edges: dict[str, HistoricalHyperedge] = {}

    @property
    def nodes(self) -> tuple[HistoricalNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[HistoricalHyperedge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def add_node(self, node: HistoricalNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate node_id: {node.node_id}")
        self._nodes[node.node_id] = node

    def add_edge(self, edge: HistoricalHyperedge, *, require_existing_nodes: bool = True) -> None:
        if edge.edge_id in self._edges:
            raise ValueError(f"duplicate edge_id: {edge.edge_id}")
        if require_existing_nodes:
            missing = sorted((set(edge.source_node_ids) | set(edge.target_node_ids)) - set(self._nodes))
            if missing:
                raise KeyError(f"edge references missing nodes: {missing}")
        self._edges[edge.edge_id] = edge

    def get_node(self, node_id: str) -> HistoricalNode:
        return self._nodes[node_id]

    def get_edge(self, edge_id: str) -> HistoricalHyperedge:
        return self._edges[edge_id]

    def incident_edges(self, node_id: str) -> tuple[HistoricalHyperedge, ...]:
        if node_id not in self._nodes:
            raise KeyError(node_id)
        return tuple(
            edge
            for edge in self.edges
            if node_id in edge.source_node_ids or node_id in edge.target_node_ids
        )

    def successors(self, node_id: str, kinds: Iterable[EdgeKind] | None = None) -> tuple[str, ...]:
        allowed = set(kinds) if kinds is not None else None
        result: set[str] = set()
        for edge in self.edges:
            if node_id in edge.source_node_ids and (allowed is None or edge.kind in allowed):
                result.update(edge.target_node_ids)
        return tuple(sorted(result))

    def predecessors(self, node_id: str, kinds: Iterable[EdgeKind] | None = None) -> tuple[str, ...]:
        allowed = set(kinds) if kinds is not None else None
        result: set[str] = set()
        for edge in self.edges:
            if node_id in edge.target_node_ids and (allowed is None or edge.kind in allowed):
                result.update(edge.source_node_ids)
        return tuple(sorted(result))

    def reachable(self, start_node_ids: Iterable[str], *, max_depth: int | None = None) -> tuple[str, ...]:
        starts = tuple(start_node_ids)
        missing = sorted(set(starts) - set(self._nodes))
        if missing:
            raise KeyError(f"missing start nodes: {missing}")
        queue = deque((node_id, 0) for node_id in starts)
        seen = set(starts)
        while queue:
            node_id, depth = queue.popleft()
            if max_depth is not None and depth >= max_depth:
                continue
            for successor in self.successors(node_id):
                if successor not in seen:
                    seen.add(successor)
                    queue.append((successor, depth + 1))
        return tuple(sorted(seen))

    def induced_subgraph(self, node_ids: Iterable[str]) -> "HistoricalHypergraph":
        selected = set(node_ids)
        missing = sorted(selected - set(self._nodes))
        if missing:
            raise KeyError(f"missing nodes: {missing}")
        graph = HistoricalHypergraph()
        for node_id in sorted(selected):
            graph.add_node(self._nodes[node_id])
        for edge in self.edges:
            endpoints = set(edge.source_node_ids) | set(edge.target_node_ids)
            if endpoints <= selected:
                graph.add_edge(edge)
        return graph

    def temporal_slice(self, layers: Iterable[TemporalLayer]) -> "HistoricalHypergraph":
        selected_layers = set(layers)
        selected = {
            node.node_id
            for node in self.nodes
            if not node.temporal_layers or selected_layers.intersection(node.temporal_layers)
        }
        return self.induced_subgraph(selected)

    def branch_nodes(self) -> tuple[HistoricalNode, ...]:
        return tuple(node for node in self.nodes if node.kind is NodeKind.BRANCH)

    def audit(self) -> GraphAudit:
        dangling: set[str] = set()
        signatures: dict[tuple[object, ...], list[str]] = defaultdict(list)
        incident: set[str] = set()
        for edge in self.edges:
            endpoints = set(edge.source_node_ids) | set(edge.target_node_ids)
            dangling.update(endpoints - set(self._nodes))
            incident.update(endpoints & set(self._nodes))
            signature = (
                edge.kind.value,
                edge.source_node_ids,
                edge.target_node_ids,
                edge.valid_from_year,
                edge.valid_to_year,
            )
            signatures[signature].append(edge.edge_id)
        duplicate_signatures = tuple(
            sorted(edge_id for ids in signatures.values() if len(ids) > 1 for edge_id in ids)
        )
        orphans = tuple(sorted(set(self._nodes) - incident))
        digest = content_hash({"nodes": self.nodes, "edges": self.edges})
        return GraphAudit(
            valid=not dangling and not duplicate_signatures,
            node_count=len(self._nodes),
            edge_count=len(self._edges),
            dangling_node_ids=tuple(sorted(dangling)),
            duplicate_edge_signatures=duplicate_signatures,
            orphan_node_ids=orphans,
            digest=digest,
        )

    def to_graphml(self) -> str:
        """Export a deterministic incidence-expanded GraphML representation.

        Hyperedges become explicit nodes prefixed with ``hyperedge::``. This
        preserves many-to-many relations in graph tools that only support
        binary edges.
        """
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <key id="kind" for="all" attr.name="kind" attr.type="string"/>',
            '  <key id="role" for="edge" attr.name="role" attr.type="string"/>',
            '  <graph id="omega-histoscience" edgedefault="directed">',
        ]
        for node in self.nodes:
            lines.extend(
                [
                    f'    <node id="{escape(node.node_id)}">',
                    f'      <data key="label">{escape(node.label)}</data>',
                    f'      <data key="kind">{escape(node.kind.value)}</data>',
                    '    </node>',
                ]
            )
        binary_index = 0
        for edge in self.edges:
            hyperedge_id = f"hyperedge::{edge.edge_id}"
            lines.extend(
                [
                    f'    <node id="{escape(hyperedge_id)}">',
                    f'      <data key="label">{escape(edge.edge_id)}</data>',
                    f'      <data key="kind">{escape(edge.kind.value)}</data>',
                    '    </node>',
                ]
            )
            for source in edge.source_node_ids:
                lines.extend(
                    [
                        f'    <edge id="e{binary_index}" source="{escape(source)}" target="{escape(hyperedge_id)}">',
                        '      <data key="role">source</data>',
                        '    </edge>',
                    ]
                )
                binary_index += 1
            for target in edge.target_node_ids:
                lines.extend(
                    [
                        f'    <edge id="e{binary_index}" source="{escape(hyperedge_id)}" target="{escape(target)}">',
                        '      <data key="role">target</data>',
                        '    </edge>',
                    ]
                )
                binary_index += 1
        lines.extend(["  </graph>", "</graphml>", ""])
        return "\n".join(lines)

    def iter_paths(self, start: str, target: str, *, max_depth: int = 6) -> Iterator[tuple[str, ...]]:
        if start not in self._nodes or target not in self._nodes:
            raise KeyError("start and target must exist")
        stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
        while stack:
            current, path = stack.pop()
            if current == target:
                yield path
                continue
            if len(path) - 1 >= max_depth:
                continue
            for successor in reversed(self.successors(current)):
                if successor not in path:
                    stack.append((successor, path + (successor,)))
