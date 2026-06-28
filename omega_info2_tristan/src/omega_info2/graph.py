"""Claim-evidence-residue graph primitives for Ω-INFO²-T."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import InfoObject


@dataclass(slots=True)
class Info2Node:
    id: str
    kind: str
    label: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Info2Edge:
    kind: str
    source: str
    target: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Info2Graph:
    nodes: dict[str, Info2Node] = field(default_factory=dict)
    edges: list[Info2Edge] = field(default_factory=list)

    def add_node(self, node_id: str, kind: str, label: str, **data: Any) -> None:
        self.nodes[node_id] = Info2Node(id=node_id, kind=kind, label=label, data=data)

    def add_edge(self, kind: str, source: str, target: str, **data: Any) -> None:
        self.edges.append(Info2Edge(kind=kind, source=source, target=target, data=data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [asdict(node) for node in self.nodes.values()],
            "edges": [asdict(edge) for edge in self.edges],
        }

    @classmethod
    def from_info_object(cls, obj: InfoObject) -> "Info2Graph":
        graph = cls()
        root_id = obj.id
        graph.add_node(root_id, "info_object", obj.id, oak_status=obj.oak.status.value)

        if obj.meta.source:
            source_id = f"source:{obj.id}"
            graph.add_node(source_id, "source", obj.meta.source, author=obj.meta.author, license=obj.meta.license)
            graph.add_edge("DERIVES_FROM", root_id, source_id)

        for i, claim in enumerate(obj.claims):
            claim_id = f"claim:{obj.id}:{i}"
            graph.add_node(
                claim_id,
                "claim",
                claim.text,
                domain=claim.domain,
                uncertainty=claim.uncertainty,
                oak_status=claim.oak_status.value,
                next_test=claim.next_test,
            )
            graph.add_edge("CONTAINS", root_id, claim_id)
            if claim.source_id:
                graph.add_edge("SUPPORTED_BY", claim_id, claim.source_id)
            for evidence_id in claim.evidence_ids:
                graph.add_edge("SUPPORTED_BY", claim_id, evidence_id)
            for counter_id in claim.counterevidence_ids:
                graph.add_edge("CONTRADICTED_BY", claim_id, counter_id)

        for concept in obj.concepts:
            concept_id = f"concept:{obj.id}:{concept}"
            graph.add_node(concept_id, "concept", concept)
            graph.add_edge("MENTIONS", root_id, concept_id)

        for item in obj.oak.residue:
            residue_id = f"residue:{obj.id}:{len(graph.nodes)}"
            graph.add_node(residue_id, "residue", item)
            graph.add_edge("HAS_RESIDUE", root_id, residue_id)

        if obj.action.next_action:
            action_id = f"action:{obj.id}"
            graph.add_node(action_id, "action", obj.action.next_action, route=obj.action.recommended_route.value)
            graph.add_edge("RECOMMENDS", root_id, action_id)

        return graph
