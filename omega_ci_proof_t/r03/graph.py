from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping

from .models import EpistemicEdge, EpistemicGraph, EpistemicNode, InvalidationResult, sorted_unique

_PROPAGATING_RELATIONS = {"depends_on", "assumes", "supported_by", "verified_by", "produced_by", "derived_from", "governs"}
_CYCLE_RELATIONS = {"depends_on", "assumes"}


class EpistemicGraphEngine:
    def __init__(self, graph: EpistemicGraph) -> None:
        self.graph = graph
        self.nodes = {node.node_id: node for node in graph.nodes}
        self._validate()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "EpistemicGraphEngine":
        nodes = tuple(
            EpistemicNode(
                node_id=str(item["node_id"]),
                kind=str(item["kind"]),
                label=str(item["label"]),
                status=str(item.get("status", "UNKNOWN")),
                criticality=int(item.get("criticality", 1)),
                metadata=dict(item.get("metadata", {})),
            )
            for item in raw.get("nodes", [])
        )
        edges = tuple(
            EpistemicEdge(
                source=str(item["source"]),
                target=str(item["target"]),
                relation=str(item["relation"]),
                weight=float(item.get("weight", 1.0)),
                metadata=dict(item.get("metadata", {})),
            )
            for item in raw.get("edges", [])
        )
        return cls(EpistemicGraph(nodes=nodes, edges=edges))

    def _validate(self) -> None:
        ids = [node.node_id for node in self.graph.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate epistemic node IDs")
        for edge in self.graph.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError(f"edge references unknown node: {edge.source} -> {edge.target}")
        self._assert_dependency_acyclic()

    def _assert_dependency_acyclic(self) -> None:
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = {node_id: 0 for node_id in self.nodes}
        for edge in self.graph.edges:
            if edge.relation in _CYCLE_RELATIONS:
                adjacency[edge.source].append(edge.target)
                indegree[edge.target] += 1
        queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for target in sorted(adjacency[current]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if visited != len(self.nodes):
            raise ValueError("dependency/assumption cycle detected")

    def stats(self) -> dict[str, Any]:
        by_kind: dict[str, int] = defaultdict(int)
        by_relation: dict[str, int] = defaultdict(int)
        for node in self.graph.nodes:
            by_kind[node.kind] += 1
        for edge in self.graph.edges:
            by_relation[edge.relation] += 1
        return {
            "graph_id": self.graph.graph_id,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "nodes_by_kind": dict(sorted(by_kind.items())),
            "edges_by_relation": dict(sorted(by_relation.items())),
            "remote_mutations": 0,
        }

    def invalidate(self, changed_node_ids: Iterable[str]) -> InvalidationResult:
        triggers = sorted_unique(tuple(changed_node_ids))
        unknown = [node_id for node_id in triggers if node_id not in self.nodes]
        if unknown:
            raise KeyError(f"unknown changed nodes: {', '.join(unknown)}")

        reverse: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for edge in self.graph.edges:
            if edge.relation in _PROPAGATING_RELATIONS:
                # source epistemically depends on target, so target changes invalidate source.
                reverse[edge.target].append((edge.source, edge.relation))

        invalidated = set(triggers)
        paths: dict[str, tuple[str, ...]] = {node_id: (node_id,) for node_id in triggers}
        reasons: dict[str, set[str]] = {node_id: {"direct_change"} for node_id in triggers}
        queue = deque(triggers)
        while queue:
            current = queue.popleft()
            for dependent, relation in sorted(reverse[current]):
                reasons.setdefault(dependent, set()).add(f"{relation}:{current}")
                candidate_path = (*paths[current], dependent)
                if dependent not in invalidated:
                    invalidated.add(dependent)
                    paths[dependent] = candidate_path
                    queue.append(dependent)
                elif len(candidate_path) < len(paths.get(dependent, candidate_path)):
                    paths[dependent] = candidate_path
        return InvalidationResult(
            trigger_node_ids=triggers,
            invalidated_node_ids=tuple(sorted(invalidated)),
            propagation_paths={key: paths[key] for key in sorted(paths)},
            reasons={key: tuple(sorted(value)) for key, value in sorted(reasons.items())},
            graph_id=self.graph.graph_id,
        )
