from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .core import GRAPH_KINDS, Envelope, GraphEdge, ObjectRef, stable_digest


@dataclass
class ResearchGraphKernel:
    """Six graph kernel with typed cross-graph references.

    The graphs are deliberately distinct. A knowledge claim is not a capability,
    a work item is not evidence, and provenance is not value.
    """

    nodes: dict[str, dict[str, Envelope]] = field(
        default_factory=lambda: {kind: {} for kind in GRAPH_KINDS}
    )
    edges: list[GraphEdge] = field(default_factory=list)

    def add(self, envelope: Envelope) -> ObjectRef:
        bucket = self.nodes[envelope.graph]
        key = envelope.ref.key
        existing = bucket.get(key)
        if existing is not None and existing.content_hash != envelope.content_hash:
            raise ValueError(f"conflicting object revision for {key}")
        bucket[key] = envelope
        return envelope.ref

    def get(self, ref: ObjectRef) -> Envelope | None:
        return self.nodes.get(ref.graph, {}).get(ref.key)

    def link(self, edge: GraphEdge) -> str:
        if self.get(edge.source) is None:
            raise KeyError(f"missing source: {edge.source.key}")
        if self.get(edge.target) is None:
            raise KeyError(f"missing target: {edge.target.key}")
        for evidence in edge.evidence_refs:
            if self.get(evidence) is None:
                raise KeyError(f"missing evidence ref: {evidence.key}")
        if all(existing.fingerprint != edge.fingerprint for existing in self.edges):
            self.edges.append(edge)
        return edge.fingerprint

    def refs(self, graph: str | None = None) -> tuple[ObjectRef, ...]:
        kinds = (graph,) if graph else GRAPH_KINDS
        out: list[ObjectRef] = []
        for kind in kinds:
            if kind not in GRAPH_KINDS:
                raise ValueError(kind)
            out.extend(item.ref for item in self.nodes[kind].values())
        return tuple(sorted(out, key=lambda item: item.key))

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        for edge in self.edges:
            if self.get(edge.source) is None:
                errors.append(f"missing source {edge.source.key}")
            if self.get(edge.target) is None:
                errors.append(f"missing target {edge.target.key}")
            for evidence in edge.evidence_refs:
                if self.get(evidence) is None:
                    errors.append(f"missing evidence {evidence.key}")
        counts = {kind: len(self.nodes[kind]) for kind in GRAPH_KINDS}
        return {
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
            "node_counts": counts,
            "edge_count": len(self.edges),
            "fingerprint": self.fingerprint,
        }

    @property
    def fingerprint(self) -> str:
        payload = {
            "nodes": {
                kind: [self.nodes[kind][key].to_dict() for key in sorted(self.nodes[kind])]
                for kind in GRAPH_KINDS
            },
            "edges": sorted(edge.fingerprint for edge in self.edges),
        }
        return stable_digest(payload)

    def context_packet(self, max_per_graph: int = 8) -> dict[str, Any]:
        if max_per_graph <= 0:
            raise ValueError("max_per_graph must be positive")
        graphs: dict[str, list[dict[str, Any]]] = {}
        omitted: dict[str, int] = {}
        for kind in GRAPH_KINDS:
            items = [self.nodes[kind][key] for key in sorted(self.nodes[kind])]
            selected = items[:max_per_graph]
            graphs[kind] = [
                {
                    "ref": item.ref.to_dict(),
                    "oak_state": item.oak_state,
                    "uncertainty": item.uncertainty,
                    "provenance": list(item.provenance),
                }
                for item in selected
            ]
            omitted[kind] = max(0, len(items) - len(selected))
        payload = {
            "graphs": graphs,
            "omitted": omitted,
            "edge_count": len(self.edges),
            "kernel_fingerprint": self.fingerprint,
        }
        payload["fingerprint"] = stable_digest(payload)
        return payload
