"""Dependency Graph Builder for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Creates simple dependency edges for tools, tests, schemas, policies, reports, and layers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    relation: str
    target: str


@dataclass(frozen=True)
class DependencyGraphPlan:
    edges: tuple[DependencyEdge, ...]
    orphan_sources: tuple[str, ...]


def build_dependency_graph(edges: tuple[DependencyEdge, ...], known_sources: tuple[str, ...] = ()) -> DependencyGraphPlan:
    linked_sources = {edge.source for edge in edges}
    orphan_sources = tuple(source for source in known_sources if source not in linked_sources)
    return DependencyGraphPlan(edges=edges, orphan_sources=orphan_sources)
