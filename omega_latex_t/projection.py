from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .models import DocumentIR, Node, NodeKind


DEFAULT_MIN_DEPTH: dict[NodeKind, int] = {
    NodeKind.SECTION: 0,
    NodeKind.WARNING: 0,
    NodeKind.PARAGRAPH: 1,
    NodeKind.CLAIM: 1,
    NodeKind.RESULT: 1,
    NodeKind.DEFINITION: 2,
    NodeKind.AXIOM: 2,
    NodeKind.CONJECTURE: 2,
    NodeKind.EQUATION: 2,
    NodeKind.ALGORITHM: 2,
    NodeKind.THEOREM: 3,
    NodeKind.LEMMA: 3,
    NodeKind.PROPOSITION: 3,
    NodeKind.COROLLARY: 3,
    NodeKind.EXPERIMENT: 3,
    NodeKind.FIGURE: 3,
    NodeKind.TABLE: 3,
    NodeKind.OPEN_QUESTION: 3,
    NodeKind.PROOF_SKETCH: 4,
    NodeKind.COUNTEREXAMPLE: 4,
    NodeKind.DATASET: 4,
    NodeKind.PROOF: 5,
    NodeKind.APPENDIX: 5,
}


def node_depth_range(node: Node) -> tuple[int, int | None]:
    minimum = DEFAULT_MIN_DEPTH.get(node.kind, 3) if node.min_depth is None else node.min_depth
    maximum = node.max_depth
    return minimum, maximum


def _dependency_closure(selected: set[str], by_id: dict[str, Node]) -> set[str]:
    closure = set(selected)
    frontier = list(selected)
    while frontier:
        node_id = frontier.pop()
        node = by_id.get(node_id)
        if node is None:
            continue
        for dep in node.dependencies:
            if dep in by_id and dep not in closure:
                closure.add(dep)
                frontier.append(dep)
    return closure


def _proof_obligation_closure(selected: set[str], by_id: dict[str, Node]) -> set[str]:
    closure = set(selected)
    theorem_like = {
        NodeKind.THEOREM,
        NodeKind.LEMMA,
        NodeKind.PROPOSITION,
        NodeKind.COROLLARY,
    }
    proof_like = {NodeKind.PROOF, NodeKind.PROOF_SKETCH}
    changed = True
    while changed:
        changed = False
        required = {
            node_id
            for node_id in closure
            if by_id[node_id].kind in theorem_like
            and by_id[node_id].status.lower() == "proven"
        }
        for node in by_id.values():
            if node.kind in proof_like and required.intersection(node.dependencies) and node.id not in closure:
                closure.add(node.id)
                changed = True
        dependency_closed = _dependency_closure(closure, by_id)
        if dependency_closed != closure:
            closure = dependency_closed
            changed = True
    return closure


def project_depth(doc: DocumentIR, depth: int) -> DocumentIR:
    depth = int(depth)
    if depth < 0:
        raise ValueError("depth must be >= 0")
    by_id = {node.id: node for node in doc.nodes}
    selected = set()
    policy: dict[str, Any] = {}
    for node in doc.nodes:
        minimum, maximum = node_depth_range(node)
        include = depth >= minimum and (maximum is None or depth <= maximum)
        policy[node.id] = {"min_depth": minimum, "max_depth": maximum, "selected_by_depth": include}
        if include:
            selected.add(node.id)
    closure = _proof_obligation_closure(selected, by_id)
    nodes = tuple(node for node in doc.nodes if node.id in closure)
    dependency_promoted = sorted(closure - selected)
    provenance = dict(doc.provenance)
    provenance["depth_projection"] = {
        "requested_depth": depth,
        "selected_count": len(selected),
        "closure_count": len(closure),
        "dependency_promoted": dependency_promoted,
        "policy": policy,
        "boundary": "depth projection may include deeper dependency nodes required for structural closure",
    }
    return replace(doc, meta=replace(doc.meta, depth=depth), nodes=nodes, provenance=provenance)


def project_depths(doc: DocumentIR, depths: Iterable[int]) -> dict[int, DocumentIR]:
    return {int(depth): project_depth(doc, int(depth)) for depth in depths}
