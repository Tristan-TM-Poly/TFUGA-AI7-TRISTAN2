from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .models import DocumentIR, Node


def node_hash(node: Node) -> str:
    payload = {"id": node.id, "kind": node.kind.value, "title": node.title, "content": node.content, "status": node.status, "dependencies": list(node.dependencies), "sources": list(node.sources), "symbols": [{"symbol": x.symbol, "meaning": x.meaning, "scope": x.scope, "unit": x.unit} for x in node.symbols], "result_key": node.result_key, "dimension_lhs": node.dimension_lhs, "dimension_rhs": node.dimension_rhs, "metadata": dict(node.metadata)}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def semantic_delta(before: DocumentIR, after: DocumentIR) -> dict[str, Any]:
    old = {n.id: n for n in before.nodes}; new = {n.id: n for n in after.nodes}
    added = sorted(new.keys() - old.keys()); removed = sorted(old.keys() - new.keys())
    changed = sorted(node_id for node_id in (new.keys() & old.keys()) if node_hash(old[node_id]) != node_hash(new[node_id]))
    seed = set(added) | set(removed) | set(changed)
    reverse: dict[str, set[str]] = {node_id: set() for node_id in new}
    for node in new.values():
        for dep in node.dependencies:
            if dep in reverse: reverse[dep].add(node.id)
    affected = set(x for x in seed if x in new); frontier = list(affected)
    while frontier:
        current = frontier.pop()
        for child in reverse.get(current, ()):
            if child not in affected:
                affected.add(child); frontier.append(child)
    results_changed = before.results != after.results
    if results_changed: affected.update(n.id for n in after.nodes if n.result_key)
    return {"before_semantic_hash": before.semantic_hash(), "after_semantic_hash": after.semantic_hash(), "added": added, "removed": removed, "changed": changed, "results_changed": results_changed, "affected_after": sorted(affected), "rebuild_required": bool(seed or results_changed or before.meta != after.meta), "boundary": "affected_after is dependency closure, not proof of semantic impact completeness"}
