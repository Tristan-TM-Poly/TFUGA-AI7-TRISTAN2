"""Finite representation geometry and task-dependent Pareto fronts."""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from math import inf
from typing import Iterable


@dataclass(frozen=True)
class RepresentationScore:
    name: str
    information_loss: float
    complexity: float
    error: float
    instability: float
    compute_cost: float

    def vector(self) -> tuple[float, ...]:
        return (
            self.information_loss,
            self.complexity,
            self.error,
            self.instability,
            self.compute_cost,
        )

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.vector()):
            raise ValueError("all representation costs must be non-negative")


def dominates(left: RepresentationScore, right: RepresentationScore) -> bool:
    a = left.vector()
    b = right.vector()
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def pareto_front(scores: Iterable[RepresentationScore]) -> tuple[RepresentationScore, ...]:
    points = tuple(scores)
    return tuple(
        point
        for point in points
        if not any(dominates(other, point) for other in points if other is not point)
    )


@dataclass
class RepresentationGraph:
    """Directed graph whose edge weights are declared representation losses."""

    edges: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    def add_edge(self, source: str, target: str, loss: float) -> None:
        if loss < 0:
            raise ValueError("loss must be non-negative")
        self.edges.setdefault(source, []).append((target, float(loss)))
        self.edges.setdefault(target, [])

    def shortest_loss(self, source: str, target: str) -> float:
        if source == target:
            return 0.0
        if source not in self.edges or target not in self.edges:
            return inf
        distances = {source: 0.0}
        queue: list[tuple[float, str]] = [(0.0, source)]
        while queue:
            distance, node = heappop(queue)
            if distance != distances.get(node):
                continue
            if node == target:
                return distance
            for neighbor, weight in self.edges[node]:
                candidate = distance + weight
                if candidate < distances.get(neighbor, inf):
                    distances[neighbor] = candidate
                    heappush(queue, (candidate, neighbor))
        return inf

    def mutually_recoverable(self, left: str, right: str) -> bool:
        return self.shortest_loss(left, right) < inf and self.shortest_loss(right, left) < inf
