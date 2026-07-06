"""Task Queue Mesh for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Selects the strongest safe ready item across Q0-Q10. Planning only; this module
never merges, deploys, publishes, or contacts external systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum


QUEUE_IDS = tuple(f"Q{i}" for i in range(11))
QUEUE_PRIORITY = {queue_id: index for index, queue_id in enumerate(QUEUE_IDS)}


class QueueState(StrEnum):
    READY = "ready"
    WAITING = "waiting"
    BLOCKED = "blocked"
    DONE = "done"
    REVIEW = "review"
    HOLD = "hold"


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    title: str
    queue: str
    state: QueueState = QueueState.READY
    score: float = 0
    risk: float = 0
    reversible: bool = True
    safe_alternative: str = ""

    @property
    def selectable(self) -> bool:
        return self.state == QueueState.READY and self.reversible and self.risk <= 7


@dataclass
class TaskQueueMesh:
    items: dict[str, QueueItem] = field(default_factory=dict)

    def add(self, item: QueueItem) -> None:
        if item.queue not in QUEUE_PRIORITY:
            raise ValueError(f"unknown propulsion queue: {item.queue}")
        if item.item_id in self.items:
            raise ValueError(f"duplicate queue item: {item.item_id}")
        self.items[item.item_id] = item

    def convert_blocked(self, item_id: str, safe_alternative: str) -> QueueItem:
        """Convert a blocked task into a safe alternative without dropping trace."""
        item = self.items[item_id]
        converted = replace(
            item,
            state=QueueState.READY,
            score=max(item.score, 1),
            risk=min(item.risk, 3),
            reversible=True,
            safe_alternative=safe_alternative,
        )
        self.items[item_id] = converted
        return converted

    def next_ready(self) -> QueueItem | None:
        """Return the highest scoring safe item, using queue priority as tie-breaker."""
        ready = [item for item in self.items.values() if item.selectable]
        if not ready:
            return None
        return max(ready, key=lambda item: (item.score, -QUEUE_PRIORITY[item.queue], item.item_id))

    def next_or_useful_work(self) -> QueueItem:
        """Infinite Useful Work fallback when all explicit queues are blocked."""
        selected = self.next_ready()
        if selected is not None:
            return selected
        return QueueItem(
            item_id="infinite_useful_work.next_action_note",
            title="Create traceable next-action note",
            queue="Q5",
            state=QueueState.READY,
            score=1,
            risk=0,
            reversible=True,
        )

    def waiting_items(self) -> tuple[QueueItem, ...]:
        return tuple(item for item in self.items.values() if item.state == QueueState.WAITING)

    def blocked_items(self) -> tuple[QueueItem, ...]:
        return tuple(item for item in self.items.values() if item.state == QueueState.BLOCKED)

    def held_items(self) -> tuple[QueueItem, ...]:
        return tuple(item for item in self.items.values() if item.state == QueueState.HOLD)
