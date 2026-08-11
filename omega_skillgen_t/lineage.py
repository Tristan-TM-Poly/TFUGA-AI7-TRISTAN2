from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable


def lineage_edges(specs: Iterable[dict[str, Any]]) -> list[tuple[str, str]]:
    edges = []
    for spec in specs:
        child = str(spec.get("name", "unknown"))
        lineage = spec.get("lineage", {}) or {}
        parent = lineage.get("parent")
        if parent:
            edges.append((str(parent), child))
        for item in lineage.get("parents", []) or []:
            edges.append((str(item), child))
    return edges


def lineage_audit(specs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    specs = list(specs)
    names = {str(spec.get("name", "unknown")) for spec in specs}
    edges = lineage_edges(specs)
    graph = defaultdict(list)
    indegree = {name: 0 for name in names}
    external = set()

    for parent, child in edges:
        if parent not in names:
            external.add(parent)
        if child not in names:
            continue
        graph[parent].append(child)
        indegree[child] = indegree.get(child, 0) + 1
        indegree.setdefault(parent, 0)

    queue = deque(sorted(name for name, degree in indegree.items() if degree == 0))
    visited = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for child in sorted(graph.get(node, [])):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    cyclic = sorted(
        name for name, degree in indegree.items() if degree > 0 and name in names
    )
    return {
        "skill_count": len(names),
        "edge_count": len(edges),
        "external_parents": sorted(external),
        "cycle_detected": bool(cyclic),
        "cycle_nodes": cyclic,
        "topological_order": [name for name in visited if name in names],
        "note": "Acyclic lineage supports rollback/provenance; it does not validate behavior.",
    }
