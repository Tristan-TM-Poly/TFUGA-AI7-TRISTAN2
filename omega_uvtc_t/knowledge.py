"""Content-addressed bitemporal KnowledgeMake with SCC-aware invalidation."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping


class KnowledgeStatus(str, Enum):
    VALIDATED = "VALIDATED"
    HOLD = "HOLD"
    STALE = "STALE"
    REFUTED = "REFUTED"


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    node_id: str
    kind: str
    content_hash: str
    dependencies: tuple[str, ...] = ()
    status: KnowledgeStatus = KnowledgeStatus.HOLD
    valid_time: str = ""
    known_time: str = ""
    independent_group: str = "default"


@dataclass(frozen=True, slots=True)
class KnowledgeAudit:
    valid: bool
    blockers: tuple[str, ...]
    sccs: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class InvalidationResult:
    changed: tuple[str, ...]
    invalidated: tuple[str, ...]
    nodes: tuple[KnowledgeNode, ...]


class KnowledgeMake:
    def __init__(self, nodes: Iterable[KnowledgeNode]):
        self.nodes = tuple(nodes)

    def _by_id(self) -> dict[str, KnowledgeNode]:
        return {x.node_id: x for x in self.nodes}

    def audit(self) -> KnowledgeAudit:
        blockers: list[str] = []
        ids = [n.node_id for n in self.nodes]
        dup = sorted({x for x in ids if ids.count(x) > 1})
        blockers.extend(f"duplicate:{x}" for x in dup)
        known = set(ids)
        for n in self.nodes:
            if not n.node_id:
                blockers.append("missing_node_id")
            if not n.content_hash:
                blockers.append(f"missing_hash:{n.node_id}")
            for dep in n.dependencies:
                if dep not in known:
                    blockers.append(f"missing_dependency:{n.node_id}:{dep}")
        return KnowledgeAudit(not blockers, tuple(sorted(set(blockers))), self._sccs() if not blockers else ())

    def _sccs(self) -> tuple[tuple[str, ...], ...]:
        graph = {n.node_id: tuple(n.dependencies) for n in self.nodes}
        index = 0
        stack: list[str] = []
        on_stack: set[str] = set()
        indices: dict[str, int] = {}
        low: dict[str, int] = {}
        comps: list[tuple[str, ...]] = []

        def visit(v: str) -> None:
            nonlocal index
            indices[v] = low[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)
            for w in graph[v]:
                if w not in indices:
                    visit(w)
                    low[v] = min(low[v], low[w])
                elif w in on_stack:
                    low[v] = min(low[v], indices[w])
            if low[v] == indices[v]:
                comp: list[str] = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    comp.append(w)
                    if w == v:
                        break
                comps.append(tuple(sorted(comp)))
        for node_id in sorted(graph):
            if node_id not in indices:
                visit(node_id)
        return tuple(sorted(comps))

    def invalidate(self, changed: Iterable[str]) -> InvalidationResult:
        audit = self.audit()
        if not audit.valid:
            raise ValueError(audit.blockers)
        changed_set = set(changed)
        by_id = self._by_id()
        unknown = changed_set - set(by_id)
        if unknown:
            raise KeyError(sorted(unknown))
        comp_index: dict[str, int] = {}
        for i, comp in enumerate(audit.sccs):
            for node_id in comp:
                comp_index[node_id] = i
        outgoing = {i: set() for i in range(len(audit.sccs))}
        for node in self.nodes:
            dst = comp_index[node.node_id]
            for dep in node.dependencies:
                src = comp_index[dep]
                if src != dst:
                    outgoing[src].add(dst)
        stale_comps = {comp_index[x] for x in changed_set}
        frontier = list(stale_comps)
        while frontier:
            current = frontier.pop()
            for child in outgoing[current]:
                if child not in stale_comps:
                    stale_comps.add(child)
                    frontier.append(child)
        invalidated = {node_id for i in stale_comps for node_id in audit.sccs[i]}
        updated = tuple(replace(n, status=KnowledgeStatus.STALE) if n.node_id in invalidated else n for n in self.nodes)
        return InvalidationResult(tuple(sorted(changed_set)), tuple(sorted(invalidated)), updated)


def replication_groups(nodes: Iterable[KnowledgeNode]) -> Mapping[str, tuple[str, ...]]:
    groups: dict[str, list[str]] = {}
    for node in nodes:
        groups.setdefault(node.independent_group, []).append(node.node_id)
    return {k: tuple(sorted(v)) for k, v in sorted(groups.items())}
