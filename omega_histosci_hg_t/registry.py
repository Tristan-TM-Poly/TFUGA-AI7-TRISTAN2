"""Branch, source, event, and negative-memory registry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import BranchRecord, HistoricalEvent, NegativeMemoryRecord, SourceReference, content_hash


@dataclass(frozen=True, slots=True)
class RegistryAudit:
    valid: bool
    branch_count: int
    source_count: int
    event_count: int
    negative_memory_count: int
    missing_parent_branches: tuple[str, ...]
    missing_sources: tuple[str, ...]
    missing_negative_memories: tuple[str, ...]
    parent_cycles: tuple[tuple[str, ...], ...]
    digest: str


class HistoryRegistry:
    def __init__(self) -> None:
        self.branches: dict[str, BranchRecord] = {}
        self.sources: dict[str, SourceReference] = {}
        self.events: dict[str, HistoricalEvent] = {}
        self.negative_memories: dict[str, NegativeMemoryRecord] = {}

    def add_branch(self, branch: BranchRecord) -> None:
        _add_unique(self.branches, branch.branch_id, branch, "branch")

    def add_source(self, source: SourceReference) -> None:
        _add_unique(self.sources, source.source_id, source, "source")

    def add_event(self, event: HistoricalEvent) -> None:
        _add_unique(self.events, event.event_id, event, "event")

    def add_negative_memory(self, memory: NegativeMemoryRecord) -> None:
        _add_unique(self.negative_memories, memory.memory_id, memory, "negative memory")

    def children_of(self, branch_id: str) -> tuple[BranchRecord, ...]:
        if branch_id not in self.branches:
            raise KeyError(branch_id)
        return tuple(
            self.branches[key]
            for key in sorted(self.branches)
            if branch_id in self.branches[key].parent_branch_ids
        )

    def ancestors_of(self, branch_id: str) -> tuple[str, ...]:
        if branch_id not in self.branches:
            raise KeyError(branch_id)
        result: set[str] = set()
        stack = list(self.branches[branch_id].parent_branch_ids)
        while stack:
            parent = stack.pop()
            if parent in result:
                continue
            result.add(parent)
            if parent in self.branches:
                stack.extend(self.branches[parent].parent_branch_ids)
        return tuple(sorted(result))

    def roots(self) -> tuple[BranchRecord, ...]:
        return tuple(self.branches[key] for key in sorted(self.branches) if not self.branches[key].parent_branch_ids)

    def audit(self) -> RegistryAudit:
        missing_parents: set[str] = set()
        missing_sources: set[str] = set()
        missing_memories: set[str] = set()
        for branch in self.branches.values():
            missing_parents.update(set(branch.parent_branch_ids) - set(self.branches))
            missing_sources.update(set(branch.source_ids) - set(self.sources))
            missing_memories.update(set(branch.negative_memory_ids) - set(self.negative_memories))
        for event in self.events.values():
            missing_sources.update(set(event.source_ids) - set(self.sources))
        for memory in self.negative_memories.values():
            missing_sources.update(set(memory.source_ids) - set(self.sources))
        cycles = _find_parent_cycles(self.branches)
        digest = content_hash(
            {
                "branches": tuple(self.branches[key] for key in sorted(self.branches)),
                "sources": tuple(self.sources[key] for key in sorted(self.sources)),
                "events": tuple(self.events[key] for key in sorted(self.events)),
                "negative_memories": tuple(
                    self.negative_memories[key] for key in sorted(self.negative_memories)
                ),
            }
        )
        valid = not missing_parents and not missing_sources and not missing_memories and not cycles
        return RegistryAudit(
            valid=valid,
            branch_count=len(self.branches),
            source_count=len(self.sources),
            event_count=len(self.events),
            negative_memory_count=len(self.negative_memories),
            missing_parent_branches=tuple(sorted(missing_parents)),
            missing_sources=tuple(sorted(missing_sources)),
            missing_negative_memories=tuple(sorted(missing_memories)),
            parent_cycles=cycles,
            digest=digest,
        )


def _add_unique(store: dict[str, object], identifier: str, value: object, label: str) -> None:
    if identifier in store:
        raise ValueError(f"duplicate {label} id: {identifier}")
    store[identifier] = value


def _find_parent_cycles(branches: dict[str, BranchRecord]) -> tuple[tuple[str, ...], ...]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[tuple[str, ...]] = set()

    def visit(branch_id: str, path: tuple[str, ...]) -> None:
        if branch_id in visiting:
            start = path.index(branch_id)
            cycle = path[start:] + (branch_id,)
            normalized = _normalize_cycle(cycle)
            cycles.add(normalized)
            return
        if branch_id in visited or branch_id not in branches:
            return
        visiting.add(branch_id)
        for parent in branches[branch_id].parent_branch_ids:
            visit(parent, path + (parent,))
        visiting.remove(branch_id)
        visited.add(branch_id)

    for branch_id in sorted(branches):
        visit(branch_id, (branch_id,))
    return tuple(sorted(cycles))


def _normalize_cycle(cycle: Iterable[str]) -> tuple[str, ...]:
    values = tuple(cycle)
    core = values[:-1]
    rotations = [core[index:] + core[:index] for index in range(len(core))]
    best = min(rotations)
    return best + (best[0],)
