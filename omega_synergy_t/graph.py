"""CreationGraph and closure-path primitives."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
from typing import Iterable

from .models import CreationDNA, Serializable, stable_id
from .ontology import jaccard, type_compatibility


@dataclass(slots=True)
class GraphEdge(Serializable):
    id: str
    source: str
    target: str
    relation: str
    weight: float
    evidence: list[str]
    losses: list[str]


class CreationGraph:
    def __init__(self, creations: Iterable[CreationDNA] = ()) -> None:
        self.nodes: dict[str, CreationDNA] = {item.id: item for item in creations}
        self.by_name: dict[str, str] = {item.name: item.id for item in creations}
        self.edges: dict[str, GraphEdge] = {}

    def add_edge(self, source: str, target: str, relation: str, weight: float, evidence: list[str] | None = None, losses: list[str] | None = None) -> GraphEdge:
        edge = GraphEdge(
            id=stable_id("EDG", source, target, relation),
            source=source,
            target=target,
            relation=relation,
            weight=max(0.0, min(1.0, weight)),
            evidence=evidence or [],
            losses=losses or [],
        )
        self.edges[edge.id] = edge
        return edge

    def infer_edges(self) -> None:
        creations = list(self.nodes.values())
        for left in creations:
            for right in creations:
                if left.id == right.id:
                    continue
                matches: list[float] = []
                evidence: list[str] = []
                for capability in left.capabilities:
                    for need in right.needs:
                        compatibility = type_compatibility(capability.output_types, need.desired_output_types)
                        if compatibility >= 0.35:
                            matches.append(compatibility)
                            evidence.extend(capability.provenance + need.provenance)
                if matches:
                    self.add_edge(left.id, right.id, "provides_for", max(matches), sorted(set(evidence))[:12])
                semantic = jaccard(left.tokens[:40], right.tokens[:40])
                if semantic >= 0.18:
                    self.add_edge(left.id, right.id, "resonates_with", semantic, left.paths[:2] + right.paths[:2])

    def adjacency(self, relations: set[str] | None = None) -> dict[str, list[GraphEdge]]:
        result: dict[str, list[GraphEdge]] = defaultdict(list)
        for edge in self.edges.values():
            if relations is None or edge.relation in relations:
                result[edge.source].append(edge)
        return result

    def shortest_path(self, source: str, target: str, relations: set[str] | None = None) -> list[str]:
        if source == target:
            return [source]
        adjacency = self.adjacency(relations)
        queue = deque([(source, [source])])
        seen = {source}
        while queue:
            current, path = queue.popleft()
            for edge in adjacency.get(current, []):
                if edge.target == target:
                    return path + [target]
                if edge.target not in seen:
                    seen.add(edge.target)
                    queue.append((edge.target, path + [edge.target]))
        return []

    def unresolved_needs(self) -> dict[str, list[str]]:
        incoming: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges.values():
            if edge.relation == "provides_for":
                incoming[edge.target].add(edge.source)
        return {
            creation.id: [need.id for need in creation.needs]
            for creation in self.nodes.values()
            if creation.needs and not incoming.get(creation.id)
        }

    def to_dict(self) -> dict:
        return {
            "nodes": [node.to_dict() for node in sorted(self.nodes.values(), key=lambda item: item.name)],
            "edges": [edge.to_dict() for edge in sorted(self.edges.values(), key=lambda item: item.id)],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n"

    def to_dot(self) -> str:
        lines = ["digraph omega_synergy_t {", "  rankdir=LR;"]
        for node in sorted(self.nodes.values(), key=lambda item: item.name):
            label = node.name.replace('"', "'")
            lines.append(f'  "{node.id}" [label="{label}"];')
        for edge in sorted(self.edges.values(), key=lambda item: item.id):
            lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.relation}:{edge.weight:.2f}"];')
        lines.append("}")
        return "\n".join(lines) + "\n"
