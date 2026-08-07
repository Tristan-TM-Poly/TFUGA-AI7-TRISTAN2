from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import SummaryEdge, SummaryNode

EXPLICIT_RELATIONS = {
    "IMPLEMENTS",
    "BENCHMARKS",
    "CONTRADICTS",
    "SUPERSEDES",
    "GENERATED_FROM",
    "DEPENDS_ON",
}
RELATION_MANIFESTS = (
    ".omega/relations.json",
    "omega_relations.json",
    "relations/omega_relations.json",
)


def _unique(edges: Iterable[SummaryEdge]) -> list[SummaryEdge]:
    seen: set[tuple[str, str, str]] = set()
    out = []
    for edge in edges:
        key = (edge.source, edge.relation, edge.target)
        if key in seen:
            continue
        seen.add(key)
        out.append(edge)
    return out


def _explicit_manifest_edges(root: Path, nodes: list[SummaryNode]) -> list[SummaryEdge]:
    systems = {node.path: node.id for node in nodes if node.kind == "system"}
    edges: list[SummaryEdge] = []
    for relative in RELATION_MANIFESTS:
        path = root / relative
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entries = payload.get("relations", payload) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict):
                continue
            source = str(item.get("source", ""))
            target = str(item.get("target", ""))
            relation = str(item.get("relation", "")).upper()
            if relation not in EXPLICIT_RELATIONS:
                continue
            if source not in systems or target not in systems or source == target:
                continue
            edges.append(SummaryEdge(systems[source], systems[target], relation))
    return edges


def _benchmark_edges(nodes: list[SummaryNode], edges: list[SummaryEdge]) -> list[SummaryEdge]:
    by_id = {node.id: node for node in nodes}
    out: list[SummaryEdge] = []
    for edge in edges:
        if edge.relation not in {"TESTS", "VALIDATES", "SUPPORTS"}:
            continue
        target = by_id.get(edge.target)
        if not target:
            continue
        marker = f"{target.path} {target.title}".casefold()
        if "benchmark" in marker or "oakbench" in marker or "/bench" in marker or "test_bench" in marker:
            out.append(SummaryEdge(edge.source, edge.target, "BENCHMARKS"))
    return out


def enrich_relations(root: str | Path, nodes: list[SummaryNode], edges: list[SummaryEdge]) -> list[SummaryEdge]:
    """Add evidence-bounded relation types without semantic guessing.

    Strong semantic system-to-system relations are accepted only from an explicit
    relation manifest. BENCHMARKS may also be derived from already-linked validation
    artifacts whose names explicitly identify them as benchmark/OAKBench files.
    """

    root_path = Path(root).resolve()
    enriched = list(edges)
    enriched.extend(_benchmark_edges(nodes, edges))
    enriched.extend(_explicit_manifest_edges(root_path, nodes))
    return sorted(_unique(enriched), key=lambda edge: (edge.source, edge.relation, edge.target))
