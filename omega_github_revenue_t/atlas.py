from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .transparency import digest_payload


@dataclass(frozen=True)
class AtlasNode:
    node_id: str
    kind: str
    label: str
    status: str
    evidence_level: str
    public: bool


@dataclass(frozen=True)
class AtlasEdge:
    edge_id: str
    source: str
    target: str
    relation: str


def build_revenue_atlas(
    nodes: Iterable[AtlasNode],
    edges: Iterable[AtlasEdge],
) -> dict[str, Any]:
    node_list = sorted(nodes, key=lambda item: item.node_id)
    edge_list = sorted(edges, key=lambda item: item.edge_id)
    identifiers = {item.node_id for item in node_list}
    if len(identifiers) != len(node_list):
        raise ValueError("duplicate atlas node_id")
    for edge in edge_list:
        if edge.source not in identifiers or edge.target not in identifiers:
            raise ValueError(f"edge references unknown node: {edge.edge_id}")
    body = {
        "schema": "omega-github-revenue-atlas-r02",
        "nodes": [asdict(item) for item in node_list],
        "edges": [asdict(item) for item in edge_list],
        "non_claims": [
            "graph connectivity is not scientific proof",
            "economic routing is not a valuation or income forecast",
            "public status requires separate IP, privacy, safety, and evidence gates",
        ],
    }
    return body | {"atlas_hash": digest_payload(body)}


def default_system_atlas() -> dict[str, Any]:
    names = [
        ("corpus", "source", "TFUGA corpus"),
        ("asset", "artifact", "Revenue-capable artifact"),
        ("ipgate", "gate", "IP and disclosure gate"),
        ("proof", "evidence", "Proof compiler"),
        ("demo", "artifact", "Reproducible demonstration"),
        ("profile", "interface", "GitHub Sponsors profile"),
        ("offer", "commercial", "Bounded offer"),
        ("pilot", "experiment", "Consented pilot"),
        ("transaction", "evidence", "Observed transaction"),
        ("reconcile", "gate", "Provider reconciliation"),
        ("mminus", "memory", "Negative memory"),
        ("allocation", "decision", "Evidence-weighted allocation"),
    ]
    nodes = [
        AtlasNode(
            identifier,
            kind,
            label,
            "R0.2",
            "prototype",
            identifier not in {"transaction"},
        )
        for identifier, kind, label in names
    ]
    relations = [
        ("corpus", "asset", "extracts"),
        ("asset", "ipgate", "classified_by"),
        ("ipgate", "proof", "admits"),
        ("proof", "demo", "supports"),
        ("demo", "profile", "communicated_by"),
        ("demo", "offer", "bounded_as"),
        ("offer", "pilot", "tested_by"),
        ("pilot", "transaction", "may_generate"),
        ("transaction", "reconcile", "verified_by"),
        ("pilot", "mminus", "updates"),
        ("reconcile", "allocation", "informs"),
        ("mminus", "allocation", "constrains"),
    ]
    edges = [
        AtlasEdge(f"E-{index:03d}", source, target, relation)
        for index, (source, target, relation) in enumerate(relations, 1)
    ]
    return build_revenue_atlas(nodes, edges)
