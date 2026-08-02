"""HGFM-style projection of family cells and evidence templates."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import EvidenceTemplate, FamilyCell


def build_hypergraph(cells: Iterable[FamilyCell], evidence: Iterable[EvidenceTemplate]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    hyperedges: list[dict[str, Any]] = []
    family_ids: set[str] = set()
    for cell in cells:
        family_ids.add(cell.id)
        nodes.append({"id": cell.id, "kind": "family_cell", "score": cell.compatibility_score})
        coordinate = cell.coordinate.to_dict()
        for axis, value in coordinate.items():
            node_id = f"VOCAB::{axis}::{value}"
            nodes.append({"id": node_id, "kind": "vocabulary", "axis": axis, "value": value})
            hyperedges.append({"kind": "has_coordinate", "members": [cell.id, node_id]})
    for item in evidence:
        if item.family_id not in family_ids:
            raise ValueError(f"orphan evidence: {item.id}")
        nodes.append({"id": item.id, "kind": "evidence_template", "status": item.status})
        hyperedges.append({"kind": "evaluates", "members": [item.id, item.family_id]})
    dedup = {node["id"]: node for node in nodes}
    return {
        "nodes": [dedup[key] for key in sorted(dedup)],
        "hyperedges": hyperedges,
        "oak_boundary": "Generated relations are reviewable candidates, not empirical evidence.",
    }
