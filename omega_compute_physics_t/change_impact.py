"""Propagate commit-level file changes through a static call graph.

The result is a benchmark-priority heuristic: directly changed functions are
highest priority, callers receive decayed upstream impact, and changed files
outside the resolved call graph remain explicit unresolved impact evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import deque
from typing import Any

from .call_graph import CallGraphReport
from .snapshot_ledger import SnapshotDiff


@dataclass(frozen=True)
class ImpactedNode:
    node: str
    distance: int
    impact_score: float
    reason: str


@dataclass(frozen=True)
class ChangeImpactReport:
    repository: str
    old_commit: str
    new_commit: str
    impacted_nodes: tuple[ImpactedNode, ...]
    unresolved_changed_files: tuple[str, ...]
    changed_files: tuple[str, ...]
    status: str = "static-change-impact-candidate"
    oak_warning: str = (
        "Impact propagation follows a partial static call graph. It prioritizes "
        "remeasurement but does not prove semantic or performance impact."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "impacted_nodes": [asdict(row) for row in self.impacted_nodes],
        }


def propagate_change_impact(
    snapshot_diff: SnapshotDiff,
    call_graph: CallGraphReport,
    *,
    max_hops: int = 4,
    decay: float = 0.55,
) -> ChangeImpactReport:
    if max_hops < 0:
        raise ValueError("max_hops must be non-negative")
    if not 0.0 < decay <= 1.0:
        raise ValueError("decay must be in (0, 1]")

    changed_files = tuple(sorted(set(snapshot_diff.added) | set(snapshot_diff.removed) | set(snapshot_diff.changed)))
    nodes_by_module: dict[str, list[str]] = {}
    for node in call_graph.nodes:
        module = node.split(":", 1)[0]
        nodes_by_module.setdefault(module, []).append(node)

    direct: set[str] = set()
    unresolved: list[str] = []
    for path in changed_files:
        matches = nodes_by_module.get(path, [])
        if matches:
            direct.update(matches)
        else:
            unresolved.append(path)

    reverse: dict[str, set[str]] = {node: set() for node in call_graph.nodes}
    for edge in call_graph.edges:
        reverse.setdefault(edge.callee, set()).add(edge.caller)

    best_distance: dict[str, int] = {}
    queue = deque()
    for node in sorted(direct):
        best_distance[node] = 0
        queue.append(node)
    while queue:
        node = queue.popleft()
        distance = best_distance[node]
        if distance >= max_hops:
            continue
        for caller in sorted(reverse.get(node, set())):
            candidate = distance + 1
            if caller not in best_distance or candidate < best_distance[caller]:
                best_distance[caller] = candidate
                queue.append(caller)

    impacted = tuple(
        sorted(
            (
                ImpactedNode(
                    node=node,
                    distance=distance,
                    impact_score=(decay ** distance) * (1.0 + 0.05 * call_graph.fan_in.get(node, 0)),
                    reason="directly changed module" if distance == 0 else f"caller within {distance} hop(s) of changed code",
                )
                for node, distance in best_distance.items()
            ),
            key=lambda row: (-row.impact_score, row.distance, row.node),
        )
    )
    return ChangeImpactReport(
        repository=snapshot_diff.repository,
        old_commit=snapshot_diff.old_commit,
        new_commit=snapshot_diff.new_commit,
        impacted_nodes=impacted,
        unresolved_changed_files=tuple(sorted(unresolved)),
        changed_files=changed_files,
    )
