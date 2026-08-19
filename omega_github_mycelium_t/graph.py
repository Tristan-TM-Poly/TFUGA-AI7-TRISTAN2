from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import html
from typing import Any, Iterable

from .models import CreationRecord, PullRequestSnapshot, RepositorySnapshot


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "metadata": self.metadata,
        }


class MyceliumGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(sorted(self._edges, key=lambda item: (item.source, item.target, item.relation)))

    def add_node(self, node: GraphNode) -> None:
        existing = self._nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"conflicting node identity: {node.node_id}")
        self._nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise ValueError(f"edge endpoints must exist: {edge.source} -> {edge.target}")
        if edge not in self._edges:
            self._edges.append(edge)

    def neighbors(self, node_id: str, *, relation: str | None = None) -> tuple[str, ...]:
        if node_id not in self._nodes:
            raise KeyError(node_id)
        values: set[str] = set()
        for edge in self._edges:
            if relation is not None and edge.relation != relation:
                continue
            if edge.source == node_id:
                values.add(edge.target)
            if edge.target == node_id:
                values.add(edge.source)
        return tuple(sorted(values))

    def validate(self) -> tuple[str, ...]:
        issues: list[str] = []
        for edge in self._edges:
            if edge.source not in self._nodes:
                issues.append(f"missing source node: {edge.source}")
            if edge.target not in self._nodes:
                issues.append(f"missing target node: {edge.target}")
        return tuple(issues)

    def summary(self) -> dict[str, Any]:
        by_kind: dict[str, int] = defaultdict(int)
        by_relation: dict[str, int] = defaultdict(int)
        for node in self._nodes.values():
            by_kind[node.kind] += 1
        for edge in self._edges:
            by_relation[edge.relation] += 1
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "nodes_by_kind": dict(sorted(by_kind.items())),
            "edges_by_relation": dict(sorted(by_relation.items())),
            "validation_issues": list(self.validate()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def to_graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
            '<key id="label" for="node" attr.name="label" attr.type="string"/>',
            '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
            '<graph edgedefault="directed">',
        ]
        for node in self.nodes:
            lines.append(
                f'<node id="{html.escape(node.node_id)}"><data key="kind">{html.escape(node.kind)}</data>'
                f'<data key="label">{html.escape(node.label)}</data></node>'
            )
        for index, edge in enumerate(self.edges):
            lines.append(
                f'<edge id="e{index}" source="{html.escape(edge.source)}" target="{html.escape(edge.target)}">'
                f'<data key="relation">{html.escape(edge.relation)}</data></edge>'
            )
        lines.extend(["</graph>", "</graphml>"])
        return "\n".join(lines) + "\n"

    @classmethod
    def build(
        cls,
        repositories: Iterable[RepositorySnapshot],
        pull_requests: Iterable[PullRequestSnapshot],
        creations: Iterable[CreationRecord],
    ) -> "MyceliumGraph":
        graph = cls()
        repositories = tuple(repositories)
        pull_requests = tuple(pull_requests)
        creations = tuple(creations)
        for repository in repositories:
            node_id = f"repo:{repository.full_name}"
            graph.add_node(
                GraphNode(
                    node_id=node_id,
                    kind="repository",
                    label=repository.full_name,
                    metadata={"visibility": repository.visibility, "archived": repository.archived},
                )
            )
        for pull_request in pull_requests:
            node_id = f"pr:{pull_request.pr_id}"
            graph.add_node(
                GraphNode(
                    node_id=node_id,
                    kind="pull_request",
                    label=pull_request.title,
                    metadata={"draft": pull_request.draft, "state": pull_request.state},
                )
            )
            graph.add_edge(
                GraphEdge(
                    source=f"repo:{pull_request.repo_full_name}",
                    target=node_id,
                    relation="hosts_pr",
                    metadata={},
                )
            )
        for creation in creations:
            node_id = f"creation:{creation.creation_id}"
            graph.add_node(
                GraphNode(
                    node_id=node_id,
                    kind="creation",
                    label=creation.name,
                    metadata={"category": creation.category, "truth_status": creation.truth_status},
                )
            )
            repository_node = f"repo:{creation.canonical_repository}"
            if repository_node in graph._nodes:
                graph.add_edge(
                    GraphEdge(
                        source=repository_node,
                        target=node_id,
                        relation="defines_canon",
                        metadata={"path": creation.canonical_path},
                    )
                )
            for pr_id in creation.related_prs:
                pr_node = f"pr:{pr_id}"
                if pr_node in graph._nodes:
                    graph.add_edge(
                        GraphEdge(
                            source=pr_node,
                            target=node_id,
                            relation="implements_or_documents",
                            metadata={},
                        )
                    )
        pr_nodes = {pr.pr_id for pr in pull_requests}
        for pull_request in pull_requests:
            for dependency in pull_request.depends_on:
                if dependency in pr_nodes:
                    graph.add_edge(
                        GraphEdge(
                            source=f"pr:{dependency}",
                            target=f"pr:{pull_request.pr_id}",
                            relation="blocks_or_precedes",
                            metadata={},
                        )
                    )
        return graph


def topological_order(nodes: Iterable[str], dependencies: dict[str, Iterable[str]]) -> tuple[str, ...]:
    node_set = set(nodes)
    inbound = {node: 0 for node in node_set}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for node, prerequisites in dependencies.items():
        if node not in node_set:
            raise ValueError(f"unknown dependency target: {node}")
        for prerequisite in prerequisites:
            if prerequisite not in node_set:
                raise ValueError(f"unknown prerequisite: {prerequisite}")
            if node not in outgoing[prerequisite]:
                outgoing[prerequisite].add(node)
                inbound[node] += 1
    queue = deque(sorted(node for node, count in inbound.items() if count == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for child in sorted(outgoing[node]):
            inbound[child] -= 1
            if inbound[child] == 0:
                queue.append(child)
    if len(ordered) != len(node_set):
        raise ValueError("dependency cycle detected")
    return tuple(ordered)
