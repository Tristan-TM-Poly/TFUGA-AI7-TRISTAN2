"""Semantic OAK validation for HGFM proof/criterion graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


PROOF_GRADE = {"PROVED", "KNOWN_THEOREM"}
KNOWN_STATUSES = {
    "OPEN",
    "OBSERVED",
    "NUMERICALLY_VERIFIED",
    "SYMBOLICALLY_DERIVED",
    "KNOWN_THEOREM",
    "CONJECTURE",
    "PROVED",
    "REFUTED",
}
NON_PROMOTING_RELATIONS = {
    "does_not_prove",
    "research_path_only",
    "compress_candidates",
    "motivates_positive_moment_constraints",
    "target_theorem",
}


def validate_proof_graph(graph: Mapping[str, Any]) -> list[str]:
    """Return semantic/OAK validation errors for a proof graph.

    This checks graph integrity and a conservative proof-leaf rule. It does not
    verify mathematical truth.
    """

    errors: list[str] = []
    nodes = graph.get("nodes")
    edges = graph.get("hyperedges")
    if not isinstance(nodes, list):
        return ["nodes must be a list"]
    if not isinstance(edges, list):
        return ["hyperedges must be a list"]

    by_id: dict[str, Mapping[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, Mapping):
            errors.append("each node must be an object")
            continue
        node_id = node.get("id")
        status = node.get("status")
        if not isinstance(node_id, str) or not node_id:
            errors.append("node id must be a non-empty string")
            continue
        if node_id in by_id:
            errors.append(f"duplicate node id: {node_id}")
        by_id[node_id] = node
        if status not in KNOWN_STATUSES:
            errors.append(f"unknown status for {node_id}: {status}")

    edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, Mapping):
            errors.append("each hyperedge must be an object")
            continue
        edge_id = edge.get("id")
        sources = edge.get("sources")
        target = edge.get("target")
        relation = edge.get("relation")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append("hyperedge id must be a non-empty string")
            continue
        if edge_id in edge_ids:
            errors.append(f"duplicate hyperedge id: {edge_id}")
        edge_ids.add(edge_id)
        if not isinstance(sources, list) or not sources:
            errors.append(f"{edge_id}: sources must be a non-empty list")
            continue
        missing = [source for source in sources if source not in by_id]
        if target not in by_id:
            errors.append(f"{edge_id}: missing target node {target}")
        if missing:
            errors.append(f"{edge_id}: missing source nodes {missing}")
        if target not in by_id or missing:
            continue

        target_status = by_id[target].get("status")
        if target_status == "PROVED" and relation not in NON_PROMOTING_RELATIONS:
            weak = [
                source
                for source in sources
                if by_id[source].get("status") not in PROOF_GRADE
            ]
            if weak:
                errors.append(
                    f"{edge_id}: PROVED target {target} depends on non-proof-grade sources {weak}"
                )
    return errors


def load_and_validate_proof_graph(path: str | Path) -> list[str]:
    graph = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_proof_graph(graph)
