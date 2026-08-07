from __future__ import annotations

from collections import defaultdict

from .models import SummaryEdge, SummaryNode


class SummaryHypergraph:
    def __init__(self, nodes: list[SummaryNode], edges: list[SummaryEdge]) -> None:
        self.nodes = {node.id: node for node in nodes}
        self.edges = list(edges)
        self.children: dict[str, list[str]] = defaultdict(list)
        self.parents: dict[str, list[str]] = defaultdict(list)
        self.related: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            if edge.relation == "CONTAINS":
                self.children[edge.source].append(edge.target)
                self.parents[edge.target].append(edge.source)
            else:
                self.related[edge.source].append(edge.target)
                self.related[edge.target].append(edge.source)
        for node_id, child_ids in self.children.items():
            if node_id in self.nodes:
                self.nodes[node_id].children = sorted(set(child_ids))

    def descend(self, node_id: str, levels: int) -> list[SummaryNode]:
        if node_id not in self.nodes:
            return []
        seen = {node_id}
        frontier = [node_id]
        for _ in range(max(0, levels)):
            nxt = []
            for current in frontier:
                for child in self.children.get(current, []):
                    if child not in seen:
                        seen.add(child)
                        nxt.append(child)
            frontier = nxt
            if not frontier:
                break
        return [self.nodes[item] for item in seen if item in self.nodes]

    def focus(self, query: str | None) -> list[SummaryNode]:
        if not query:
            return list(self.nodes.values())
        needle = query.casefold()
        matched = [
            node
            for node in self.nodes.values()
            if needle in node.id.casefold()
            or needle in node.path.casefold()
            or needle in node.title.casefold()
        ]
        if not matched:
            return []
        include: set[str] = set()
        for node in matched:
            include.add(node.id)
            include.update(item.id for item in self.descend(node.id, 2))
            include.update(self.parents.get(node.id, []))
            include.update(self.related.get(node.id, []))
        return [self.nodes[item] for item in include if item in self.nodes]
