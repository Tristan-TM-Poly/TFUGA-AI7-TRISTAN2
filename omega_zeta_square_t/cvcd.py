"""CVCD-style structural compression of the RH criterion/proof HGFM.

The routines search minimal dependency-support sets.  They are graph tools, not
logical theorem provers: a minimal structural support set does not prove its
target, even when every leaf currently carries a proof-grade label.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Mapping


NON_PROMOTING_RELATIONS = {
    "does_not_prove",
    "research_path_only",
    "compress_candidates",
    "motivates_positive_moment_constraints",
    "target_theorem",
}
PROOF_GRADE = {"PROVED", "KNOWN_THEOREM"}


@dataclass(frozen=True)
class MinimalSupport:
    target: str
    leaves: tuple[str, ...]
    all_leaves_proof_grade: bool
    structural_only: bool = True
    proves_target: bool = False


def _minimalize(sets: set[frozenset[str]]) -> set[frozenset[str]]:
    ordered = sorted(sets, key=lambda s: (len(s), tuple(sorted(s))))
    kept: list[frozenset[str]] = []
    for candidate in ordered:
        if any(existing <= candidate for existing in kept):
            continue
        kept.append(candidate)
    return set(kept)


def minimal_dependency_supports(
    graph: Mapping[str, Any],
    target: str,
    *,
    excluded_relations: set[str] | None = None,
    max_sets: int = 256,
) -> list[MinimalSupport]:
    """Return inclusion-minimal structural support sets for ``target``.

    Hyperedges are interpreted as AND over their sources; alternative incoming
    hyperedges are OR alternatives. Non-promoting/research-only relations are
    excluded by default. Cycles are cut and represented by the cyclic node as a
    leaf so they cannot silently disappear.
    """

    excluded = NON_PROMOTING_RELATIONS if excluded_relations is None else excluded_relations
    nodes = {node.get("id"): node for node in graph.get("nodes", []) if isinstance(node, Mapping)}
    if target not in nodes:
        raise ValueError(f"unknown target node: {target}")

    incoming: dict[str, list[Mapping[str, Any]]] = {}
    for edge in graph.get("hyperedges", []):
        if not isinstance(edge, Mapping):
            continue
        if edge.get("relation") in excluded:
            continue
        t = edge.get("target")
        sources = edge.get("sources")
        if isinstance(t, str) and isinstance(sources, list) and sources:
            incoming.setdefault(t, []).append(edge)

    memo: dict[str, set[frozenset[str]]] = {}

    def expand(node_id: str, visiting: frozenset[str]) -> set[frozenset[str]]:
        if node_id in visiting:
            return {frozenset({node_id})}
        if node_id in memo:
            return memo[node_id]
        alternatives = incoming.get(node_id, [])
        if not alternatives:
            result = {frozenset({node_id})}
            memo[node_id] = result
            return result

        candidates: set[frozenset[str]] = set()
        next_visiting = visiting | {node_id}
        for edge in alternatives:
            source_options = [expand(str(src), next_visiting) for src in edge.get("sources", [])]
            if not source_options:
                continue
            for combo in product(*source_options):
                union: frozenset[str] = frozenset().union(*combo)
                candidates.add(union)
                if len(candidates) > max_sets * 8:
                    candidates = _minimalize(candidates)
        result = _minimalize(candidates) if candidates else {frozenset({node_id})}
        if len(result) > max_sets:
            result = set(sorted(result, key=lambda s: (len(s), tuple(sorted(s))))[:max_sets])
        memo[node_id] = result
        return result

    raw = sorted(expand(target, frozenset()), key=lambda s: (len(s), tuple(sorted(s))))
    out: list[MinimalSupport] = []
    for leaves in raw:
        statuses = [nodes.get(leaf, {}).get("status") for leaf in leaves]
        out.append(
            MinimalSupport(
                target=target,
                leaves=tuple(sorted(leaves)),
                all_leaves_proof_grade=all(status in PROOF_GRADE for status in statuses),
            )
        )
    return out


def cvcd_support_report(graph: Mapping[str, Any], target: str) -> dict[str, Any]:
    supports = minimal_dependency_supports(graph, target)
    return {
        "schema": "omega-rh-cvcd-support/1",
        "target": target,
        "structural_only": True,
        "proves_target": False,
        "support_count": len(supports),
        "supports": [
            {
                "leaves": list(item.leaves),
                "size": len(item.leaves),
                "all_leaves_proof_grade": item.all_leaves_proof_grade,
                "proves_target": False,
            }
            for item in supports
        ],
        "oak": {
            "warning": "minimal dependency support is not a proof and may encode a criterion equivalent to the target",
            "required_next_step": "audit logical direction, circularity, quantifiers, domains, and provenance for every edge",
        },
    }
