"""TaskGraph for Ω-AIT-CONTINUATION-ENGINE-T.

A simple graph of task nodes where BLOCKED is converted to SAFE_ALTERNATIVE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    READY = "ready"
    BLOCKED = "blocked"
    SAFE_ALTERNATIVE = "safe_alternative"
    DONE = "done"
    QUARANTINED = "quarantined"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class TaskNode:
    node_id: str
    title: str
    status: TaskStatus = TaskStatus.TODO
    safe_alternative: str = ""


@dataclass
class TaskGraph:
    nodes: dict[str, TaskNode] = field(default_factory=dict)
    edges: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def add_node(self, node: TaskNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate task node: {node.node_id}")
        self.nodes[node.node_id] = node

    def link(self, source_id: str, target_id: str) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("task graph endpoints must exist")
        self.edges[source_id] = self.edges.get(source_id, ()) + (target_id,)

    def convert_blocked(self, node_id: str, safe_alternative: str) -> TaskNode:
        node = self.nodes[node_id]
        if node.status != TaskStatus.BLOCKED:
            return node
        converted = TaskNode(node.node_id, node.title, TaskStatus.SAFE_ALTERNATIVE, safe_alternative)
        self.nodes[node_id] = converted
        return converted

    def blocked_nodes(self) -> tuple[TaskNode, ...]:
        return tuple(node for node in self.nodes.values() if node.status == TaskStatus.BLOCKED)
