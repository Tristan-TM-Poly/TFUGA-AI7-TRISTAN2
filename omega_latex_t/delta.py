from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .models import DocumentIR, Node


def node_hash(node: Node) -> str:
    payload = {
        "id": node.id,
        "kind": node.kind.value,
        "title": node.title,
        "content": node.content,
        "status": node.status,
        "dependencies": list(node.dependencies),
        "sources": list(node.sources),
        "symbols": [
            {"symbol": x.symbol, "meaning": x.meaning, "scope": x.scope, "unit": x.unit}
            for x in node.symbols
        ],
        "result_key": node.result_key,
        "dimension_lhs": node.dimension_lhs,
        "dimension_rhs": node.dimension_rhs,
        "math_ir": dict(node.math_ir),
        "min_depth": node.min_depth,
        "max_depth": node.max_depth,
        "metadata": dict(node.metadata),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def semantic_delta(before: DocumentIR, after: DocumentIR) -> dict[str, Any]:
    old = {n.id: n for n in before.nodes}
    new = {n.id: n for n in after.nodes}
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(
        node_id
        for node_id in (new.keys() & old.keys())
        if node_hash(old[node_id]) != node_hash(new[node_id])
    )
    seed = set(added) | set(removed) | set(changed)
    reverse: dict[str, set[str]] = {node_id: set() for node_id in new}
    for node in new.values():
        for dep in node.dependencies:
            if dep in reverse:
                reverse[dep].add(node.id)
    affected = {x for x in seed if x in new}
    frontier = list(affected)
    while frontier:
        current = frontier.pop()
        for child in reverse.get(current, ()):
            if child not in affected:
                affected.add(child)
                frontier.append(child)
    results_changed_keys = sorted(
        key
        for key in set(before.results) | set(after.results)
        if before.results.get(key) != after.results.get(key)
    )
    if results_changed_keys:
        for node in after.nodes:
            if node.result_key in results_changed_keys:
                affected.add(node.id)
                frontier.append(node.id)
        while frontier:
            current = frontier.pop()
            for child in reverse.get(current, ()):
                if child not in affected:
                    affected.add(child)
                    frontier.append(child)
    source_hash_before = {
        s.id: (s.citation, s.locator, s.sha256)
        for s in before.sources
    }
    source_hash_after = {
        s.id: (s.citation, s.locator, s.sha256)
        for s in after.sources
    }
    sources_changed = source_hash_before != source_hash_after
    if sources_changed:
        changed_source_ids = {
            key
            for key in set(source_hash_before) | set(source_hash_after)
            if source_hash_before.get(key) != source_hash_after.get(key)
        }
        source_seed = {node.id for node in after.nodes if set(node.sources) & changed_source_ids}
        affected.update(source_seed)
        frontier = list(source_seed)
        while frontier:
            current = frontier.pop()
            for child in reverse.get(current, ()):
                if child not in affected:
                    affected.add(child)
                    frontier.append(child)
    meta_changed = before.meta != after.meta
    return {
        "before_semantic_hash": before.semantic_hash(),
        "after_semantic_hash": after.semantic_hash(),
        "added": added,
        "removed": removed,
        "changed": changed,
        "results_changed": bool(results_changed_keys),
        "results_changed_keys": results_changed_keys,
        "sources_changed": sources_changed,
        "meta_changed": meta_changed,
        "affected_after": sorted(affected),
        "rebuild_required": bool(seed or results_changed_keys or sources_changed or meta_changed),
        "boundary": "affected_after is conservative structural/source/result closure, not proof of semantic-impact completeness",
    }
