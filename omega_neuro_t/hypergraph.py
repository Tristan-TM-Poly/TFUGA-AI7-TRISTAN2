from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Set

from .models import HyperEdge


@dataclass
class MultiscaleNeuroHypergraph:
    """Small multilayer relation container for research models."""

    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, HyperEdge] = field(default_factory=dict)

    def add_node(self, node_id: str) -> None:
        if not node_id:
            raise ValueError("node_id must be non-empty")
        self.nodes.add(node_id)

    def add_edge(self, edge: HyperEdge) -> None:
        missing = set(edge.members) - self.nodes
        if missing:
            raise ValueError(f"edge contains nodes not registered in the model: {sorted(missing)}")
        if edge.edge_id in self.edges:
            raise ValueError(f"duplicate edge_id: {edge.edge_id}")
        self.edges[edge.edge_id] = edge

    def select(self, *, layers: Iterable[str] | None = None, min_order: int = 2) -> Dict[str, HyperEdge]:
        allowed = set(layers) if layers is not None else None
        return {
            key: edge
            for key, edge in self.edges.items()
            if edge.order >= min_order and (allowed is None or edge.layer in allowed)
        }

    def contextual_projection(self, layer_gains: Mapping[str, float]) -> Dict[str, float]:
        projected: Dict[str, float] = {}
        for key, edge in self.edges.items():
            value = edge.weight * float(layer_gains.get(edge.layer, 0.0))
            if value != 0.0:
                projected[key] = value
        return projected

    def higher_order_fraction(self) -> float:
        if not self.edges:
            return 0.0
        return sum(edge.order > 2 for edge in self.edges.values()) / len(self.edges)
