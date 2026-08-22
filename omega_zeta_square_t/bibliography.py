"""Bibliographic OAK validation for known-theorem nodes."""

from __future__ import annotations

from typing import Any, Mapping


def validate_bibliography_ledger(
    graph: Mapping[str, Any], ledger: Mapping[str, Any]
) -> list[str]:
    """Return provenance errors linking KNOWN_THEOREM nodes to sources."""

    errors: list[str] = []
    sources = ledger.get("sources", [])
    bindings = ledger.get("claim_bindings", [])
    if not isinstance(sources, list):
        return ["bibliography sources must be a list"]
    if not isinstance(bindings, list):
        return ["claim_bindings must be a list"]

    source_by_id: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            errors.append("each bibliography source must be an object")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not sid:
            errors.append("source id must be non-empty")
            continue
        if sid in source_by_id:
            errors.append(f"duplicate source id: {sid}")
        source_by_id[sid] = source

    node_by_id = {
        node.get("id"): node
        for node in graph.get("nodes", [])
        if isinstance(node, Mapping) and isinstance(node.get("id"), str)
    }
    bound_nodes: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, Mapping):
            errors.append("each claim binding must be an object")
            continue
        node_id = binding.get("graph_node")
        source_id = binding.get("source_id")
        if node_id not in node_by_id:
            errors.append(f"binding references unknown graph node: {node_id}")
        if source_id not in source_by_id:
            errors.append(f"binding references unknown source: {source_id}")
        if node_id in node_by_id and source_id in source_by_id:
            bound_nodes.add(str(node_id))
            status = str(source_by_id[str(source_id)].get("status", ""))
            if not status.startswith("PRIMARY_SOURCE"):
                errors.append(
                    f"KNOWN theorem binding {node_id} must point to a primary-source-verified record"
                )

    for node_id, node in node_by_id.items():
        if node.get("status") == "KNOWN_THEOREM" and node_id not in bound_nodes:
            errors.append(f"KNOWN_THEOREM node lacks bibliography binding: {node_id}")
    return errors
