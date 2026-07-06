"""Task Queue Mesh for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Selects the highest-scoring ready queue item. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class QueueState(StrEnum):
    READY = "ready"
    WAITING = "waiting"
    DONE = "done"
    REVIEW = "review"


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    title: str
    queue: str
    state: QueueState = QueueState.READY
    score: int = 0


@dataclass
class TaskQueueMesh:
    items: dict[str, QueueItem] = field(default_factory=dict)

    def add(self, item: QueueItem) -> None:
        if item.item_id in self.items:
            raise ValueError(f"duplicate queue item: {item.item_id}")
        self.items[item.item_id] = item

    def next_ready(self) -> QueueItem | None:
        ready = [item for item in self.items.values() if item.state == QueueState.READY]
        if not ready:
            return None
        return max(ready, key=lambda item: item.score)

    def waiting_items(self) -> tuple[QueueItem, ...]:
        return tuple(item for item in self.items.values() if item.state == QueueState.WAITING)
