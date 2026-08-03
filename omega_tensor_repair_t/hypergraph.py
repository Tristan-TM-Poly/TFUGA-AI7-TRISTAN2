"""Hypergraph projections for representation bundles and symmetry towers."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .models import RepairBundle, SymmetryTower


@dataclass(frozen=True)
class HyperNode:
    node_id: str
    kind: str
    attributes: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.node_id, "kind": self.kind, **dict(self.attributes)}


@dataclass(frozen=True)
class HyperEdge:
    edge_id: str
    relation: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    attributes: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.edge_id,
            "relation": self.relation,
            "sources": list(self.sources),
            "targets": list(self.targets),
            **dict(self.attributes),
        }


@dataclass(frozen=True)
class RepresentationHypergraph:
    nodes: tuple[HyperNode, ...]
    hyperedges: tuple[HyperEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": "omega.tensor.repair.hypergraph.v1",
            "nodes": [node.to_dict() for node in self.nodes],
            "hyperedges": [edge.to_dict() for edge in self.hyperedges],
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        payload["sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def bundle_hypergraph(bundle: RepairBundle) -> RepresentationHypergraph:
    nodes = [
        HyperNode("input:left", "vector", {"dimension": len(bundle.input_left)}),
        HyperNode("input:right", "vector", {"dimension": len(bundle.input_right)}),
        HyperNode("tensor:full", "tensor", {"dimension": bundle.full_dimension}),
        HyperNode("tensor:residual", "residual", {"norm": bundle.residual_norm}),
    ]
    edges = [
        HyperEdge(
            "edge:outer",
            "tensor-product",
            ("input:left", "input:right"),
            ("tensor:full",),
            {},
        ),
        HyperEdge(
            "edge:reconstruct",
            "analysis-synthesis",
            tuple(),
            ("tensor:full",),
            {"residual_norm": bundle.residual_norm},
        ),
    ]
    for channel in bundle.channels:
        node_id = f"channel:{channel.name}"
        nodes.append(
            HyperNode(
                node_id,
                "representation-channel",
                {
                    "dimension": channel.dimension,
                    "symmetry": channel.symmetry,
                    "exact": channel.exact,
                    "energy": channel.energy,
                },
            )
        )
        parent = f"channel:{channel.parent}" if channel.parent else "tensor:full"
        edges.append(
            HyperEdge(
                f"edge:project:{channel.name}",
                "projects-to",
                (parent,),
                (node_id,),
                {},
            )
        )
    return RepresentationHypergraph(tuple(nodes), tuple(edges))


def tower_hypergraph(tower: SymmetryTower) -> RepresentationHypergraph:
    nodes = tuple(
        HyperNode(
            f"tower:{node.node_id}",
            "symmetry-representation",
            {"dimension": node.dimension, "symmetry": node.symmetry},
        )
        for node in tower.nodes
    )
    edges = []
    for node in tower.nodes:
        if node.children_ids:
            edges.append(
                HyperEdge(
                    f"branch:{node.node_id}",
                    "branches-into",
                    (f"tower:{node.node_id}",),
                    tuple(f"tower:{child}" for child in node.children_ids),
                    {"exact_partition": node.exact_partition},
                )
            )
    return RepresentationHypergraph(nodes, tuple(edges))
