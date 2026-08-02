"""Minimal deterministic hypergraph for worlds, narratives and production."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable

from .models import AnimeNode, HyperEdge


@dataclass
class AnimeGraph:
    nodes: dict[str, AnimeNode] = field(default_factory=dict)
    edges: dict[str, HyperEdge] = field(default_factory=dict)

    def add_node(self, node: AnimeNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f'duplicate node: {node.node_id}')
        errors = node.validate()
        if errors:
            raise ValueError('; '.join(errors))
        self.nodes[node.node_id] = node

    def add_edge(self, edge: HyperEdge) -> None:
        if edge.edge_id in self.edges:
            raise ValueError(f'duplicate edge: {edge.edge_id}')
        errors = edge.validate()
        if errors:
            raise ValueError('; '.join(errors))
        missing = (set(edge.sources) | set(edge.targets)) - set(self.nodes)
        if missing:
            raise ValueError(f'edge {edge.edge_id} references unknown nodes: {sorted(missing)}')
        self.edges[edge.edge_id] = edge

    def extend_nodes(self, nodes: Iterable[AnimeNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def extend_edges(self, edges: Iterable[HyperEdge]) -> None:
        for edge in edges:
            self.add_edge(edge)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for node in self.nodes.values():
            errors.extend(node.validate())
        for edge in self.edges.values():
            errors.extend(edge.validate())
            missing = (set(edge.sources) | set(edge.targets)) - set(self.nodes)
            if missing:
                errors.append(f'edge.{edge.edge_id}: unknown nodes {sorted(missing)}')
        return errors

    def adjacency(self, edge_type: str | None = None) -> dict[str, set[str]]:
        result: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges.values():
            if edge_type is not None and edge.edge_type != edge_type:
                continue
            for source in edge.sources:
                result[source].update(edge.targets)
        return result

    def topological_order(self, edge_type: str = 'DEPENDS_ON') -> list[str]:
        adjacency = self.adjacency(edge_type)
        indegree = {node_id: 0 for node_id in self.nodes}
        for targets in adjacency.values():
            for target in targets:
                indegree[target] += 1
        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        output: list[str] = []
        while queue:
            node = queue.popleft()
            output.append(node)
            for target in sorted(adjacency.get(node, ())):
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if len(output) != len(self.nodes):
            cyclic = sorted(node for node, degree in indegree.items() if degree > 0)
            raise ValueError(f'cycle detected for {edge_type}: {cyclic}')
        return output

    def orphan_nodes(self) -> list[str]:
        connected: set[str] = set()
        for edge in self.edges.values():
            connected.update(edge.sources)
            connected.update(edge.targets)
        return sorted(set(self.nodes) - connected)
