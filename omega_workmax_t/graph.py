from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from .models import WorkPacket


@dataclass(frozen=True)
class CriticalPath:
    seconds: float
    work_ids: tuple[str, ...]


class WorkHypergraph:
    """Deterministic dependency DAG for finite WorkPacket sets.

    Hypergraph semantics are represented by packets depending on any number of
    predecessor packets. R0.1 intentionally keeps execution edges acyclic and
    explicit; richer semantic hyperedges can remain metadata until evidenced.
    """

    def __init__(self, packets: Iterable[WorkPacket]):
        rows = tuple(packets)
        self.packets = {packet.work_id: packet for packet in rows}
        if len(self.packets) != len(rows):
            raise ValueError("duplicate work_id")
        for packet in rows:
            missing = [dep for dep in packet.dependencies if dep not in self.packets]
            if missing:
                raise ValueError(f"{packet.work_id} has missing dependencies: {missing}")
        self.children: dict[str, tuple[str, ...]] = self._build_children()
        self._topological = self._topological_order()

    def _build_children(self) -> dict[str, tuple[str, ...]]:
        children: dict[str, list[str]] = defaultdict(list)
        for packet in self.packets.values():
            for dep in packet.dependencies:
                children[dep].append(packet.work_id)
        return {work_id: tuple(sorted(children.get(work_id, []))) for work_id in self.packets}

    def _topological_order(self) -> tuple[str, ...]:
        indegree = {work_id: len(packet.dependencies) for work_id, packet in self.packets.items()}
        ready = deque(sorted(work_id for work_id, degree in indegree.items() if degree == 0))
        order: list[str] = []
        while ready:
            work_id = ready.popleft()
            order.append(work_id)
            for child in self.children[work_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
            ready = deque(sorted(ready))
        if len(order) != len(self.packets):
            raise ValueError("WorkHypergraph must be acyclic")
        return tuple(order)

    @property
    def topological_order(self) -> tuple[str, ...]:
        return self._topological

    @property
    def total_work_seconds(self) -> float:
        return sum(packet.estimated_seconds for packet in self.packets.values())

    def ready(self, completed: set[str]) -> tuple[str, ...]:
        return tuple(
            work_id
            for work_id in self._topological
            if work_id not in completed and set(self.packets[work_id].dependencies) <= completed
        )

    def blocking_power(self, work_id: str) -> int:
        if work_id not in self.packets:
            raise KeyError(work_id)
        seen: set[str] = set()
        stack = list(self.children[work_id])
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.children[current])
        return len(seen)

    def critical_path(self) -> CriticalPath:
        best_seconds: dict[str, float] = {}
        predecessor: dict[str, str | None] = {}
        for work_id in self._topological:
            packet = self.packets[work_id]
            if not packet.dependencies:
                best_seconds[work_id] = packet.estimated_seconds
                predecessor[work_id] = None
                continue
            parent = max(packet.dependencies, key=lambda dep: (best_seconds[dep], dep))
            best_seconds[work_id] = best_seconds[parent] + packet.estimated_seconds
            predecessor[work_id] = parent
        if not best_seconds:
            return CriticalPath(0.0, ())
        end = max(best_seconds, key=lambda work_id: (best_seconds[work_id], work_id))
        path: list[str] = []
        current: str | None = end
        while current is not None:
            path.append(current)
            current = predecessor[current]
        path.reverse()
        return CriticalPath(best_seconds[end], tuple(path))
