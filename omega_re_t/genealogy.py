"""Version-genealogy reconstruction from synthetic change evidence."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class VersionArtifact:
    version_id: str
    features: frozenset[str]
    behavior: Mapping[str, str]
    timestamp: str | None = None
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VersionEdge:
    parent: str
    child: str
    added_features: tuple[str, ...]
    removed_features: tuple[str, ...]
    changed_behaviors: tuple[str, ...]
    distance: float
    confidence: float


@dataclass(slots=True)
class VersionGenealogy:
    versions: dict[str, VersionArtifact] = field(default_factory=dict)
    edges: list[VersionEdge] = field(default_factory=list)

    def add_version(self, artifact: VersionArtifact) -> None:
        if artifact.version_id in self.versions:
            raise ValueError("duplicate version")
        self.versions[artifact.version_id] = artifact

    def add_edge(self, edge: VersionEdge) -> None:
        if edge.parent not in self.versions or edge.child not in self.versions:
            raise ValueError("edge references unknown version")
        if edge.parent == edge.child:
            raise ValueError("self ancestry is invalid")
        self.edges.append(edge)
        if self.has_cycle():
            self.edges.pop()
            raise ValueError("edge introduces genealogy cycle")

    def parents(self, version_id: str) -> tuple[str, ...]:
        return tuple(sorted(edge.parent for edge in self.edges if edge.child == version_id))

    def children(self, version_id: str) -> tuple[str, ...]:
        return tuple(sorted(edge.child for edge in self.edges if edge.parent == version_id))

    def has_cycle(self) -> bool:
        indegree = {version: 0 for version in self.versions}
        for edge in self.edges:
            indegree[edge.child] += 1
        queue = deque(version for version, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for child in self.children(node):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        return visited != len(self.versions)

    def roots(self) -> tuple[str, ...]:
        return tuple(sorted(version for version in self.versions if not self.parents(version)))

    def lineage(self, version_id: str) -> tuple[str, ...]:
        result: list[str] = []
        current = version_id
        seen: set[str] = set()
        while True:
            if current in seen:
                raise ValueError("cycle detected")
            seen.add(current)
            result.append(current)
            parents = self.parents(current)
            if not parents:
                break
            current = parents[0]
        return tuple(reversed(result))

    def digest(self) -> str:
        payload = {
            "versions": {
                key: {
                    "features": sorted(value.features),
                    "behavior": dict(sorted(value.behavior.items())),
                    "timestamp": value.timestamp,
                    "provenance": value.provenance,
                }
                for key, value in sorted(self.versions.items())
            },
            "edges": [
                (e.parent, e.child, e.added_features, e.removed_features, e.changed_behaviors, e.distance, e.confidence)
                for e in sorted(self.edges, key=lambda item: (item.parent, item.child))
            ],
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


def version_distance(parent: VersionArtifact, child: VersionArtifact) -> VersionEdge:
    added = tuple(sorted(child.features - parent.features))
    removed = tuple(sorted(parent.features - child.features))
    keys = set(parent.behavior) | set(child.behavior)
    changed = tuple(sorted(key for key in keys if parent.behavior.get(key) != child.behavior.get(key)))
    denominator = max(1, len(parent.features | child.features) + len(keys))
    distance = (len(added) + len(removed) + len(changed)) / denominator
    confidence = 1.0 / (1.0 + distance)
    return VersionEdge(parent.version_id, child.version_id, added, removed, changed, distance, confidence)


def infer_minimum_genealogy(artifacts: Iterable[VersionArtifact]) -> VersionGenealogy:
    """Infer a deterministic minimum-distance arborescence.

    Timestamp order is used when available; otherwise identifiers provide a
    stable tie-break.  The result is a parsimonious hypothesis, not proof of
    historical ancestry.
    """
    items = tuple(artifacts)
    if not items:
        raise ValueError("at least one version is required")
    graph = VersionGenealogy()
    for item in items:
        graph.add_version(item)
    ordered = sorted(items, key=lambda item: (item.timestamp is None, item.timestamp or "", item.version_id))
    for index, child in enumerate(ordered[1:], start=1):
        candidates = [version_distance(parent, child) for parent in ordered[:index]]
        best = min(candidates, key=lambda edge: (edge.distance, edge.parent))
        graph.add_edge(best)
    return graph


@dataclass(frozen=True, slots=True)
class RegressionLocalization:
    behavior_key: str
    first_bad_version: str | None
    last_good_version: str | None
    candidate_edges: tuple[tuple[str, str], ...]
    confidence: float


def localize_regression(
    genealogy: VersionGenealogy,
    lineage: Sequence[str],
    behavior_key: str,
    expected_value: str,
) -> RegressionLocalization:
    last_good: str | None = None
    first_bad: str | None = None
    candidate_edges: list[tuple[str, str]] = []
    for previous, current in zip(lineage, lineage[1:]):
        previous_value = genealogy.versions[previous].behavior.get(behavior_key)
        current_value = genealogy.versions[current].behavior.get(behavior_key)
        if previous_value == expected_value:
            last_good = previous
        if previous_value == expected_value and current_value != expected_value:
            first_bad = current
            candidate_edges.append((previous, current))
    confidence = 1.0 if len(candidate_edges) == 1 else 0.5 if candidate_edges else 0.0
    return RegressionLocalization(behavior_key, first_bad, last_good, tuple(candidate_edges), confidence)
