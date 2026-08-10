from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .graph import WorkHypergraph
from .models import WorkPacket


@dataclass(frozen=True)
class DeduplicationResult:
    unique: tuple[WorkPacket, ...]
    duplicate_to_canonical: dict[str, str]


@dataclass(frozen=True)
class PlannedWave:
    index: int
    work_ids: tuple[str, ...]
    estimated_seconds_sum: float

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "work_ids": list(self.work_ids),
            "estimated_seconds_sum": self.estimated_seconds_sum,
        }


def deduplicate_packets(packets: Iterable[WorkPacket]) -> DeduplicationResult:
    """Exact semantic-key deduplication with deterministic representative choice."""
    buckets: dict[str, list[WorkPacket]] = {}
    for packet in packets:
        buckets.setdefault(packet.semantic_signature, []).append(packet)
    unique: list[WorkPacket] = []
    duplicates: dict[str, str] = {}
    for signature in sorted(buckets):
        group = buckets[signature]
        canonical = min(
            group,
            key=lambda packet: (
                -packet.evidence_weight,
                -packet.crystallization,
                packet.risk,
                packet.estimated_seconds,
                packet.work_id,
            ),
        )
        unique.append(canonical)
        for packet in group:
            if packet.work_id != canonical.work_id:
                duplicates[packet.work_id] = canonical.work_id
    unique.sort(key=lambda packet: packet.work_id)
    return DeduplicationResult(tuple(unique), dict(sorted(duplicates.items())))


def priority_score(packet: WorkPacket, graph: WorkHypergraph) -> float:
    """Value/information/blocking weighted by cost and risk.

    This is a transparent scheduling heuristic, not a universal utility law.
    """
    blocking = graph.blocking_power(packet.work_id)
    numerator = (
        packet.value
        * (1.0 + blocking)
        * (0.5 + packet.evidence_weight)
        * (0.5 + packet.crystallization)
        * (0.5 + packet.reuse_score)
        * (1.0 + packet.failure_probability)
    )
    denominator = packet.estimated_seconds * (1.0 + packet.risk)
    return numerator / denominator


def plan_waves(graph: WorkHypergraph, workers: int) -> tuple[PlannedWave, ...]:
    if workers < 1:
        raise ValueError("workers must be positive")
    completed: set[str] = set()
    waves: list[PlannedWave] = []
    while len(completed) < len(graph.packets):
        ready = [work_id for work_id in graph.ready(completed) if work_id not in completed]
        if not ready:
            raise RuntimeError("no schedulable work remains")
        ready.sort(key=lambda work_id: (-priority_score(graph.packets[work_id], graph), work_id))
        chosen = tuple(ready[:workers])
        waves.append(
            PlannedWave(
                index=len(waves),
                work_ids=chosen,
                estimated_seconds_sum=sum(graph.packets[work_id].estimated_seconds for work_id in chosen),
            )
        )
        completed.update(chosen)
    return tuple(waves)


def pareto_front(graph: WorkHypergraph) -> tuple[str, ...]:
    """Return non-dominated packets over value/evidence/reuse vs time/risk."""
    ids = sorted(graph.packets)

    def dominates(left: WorkPacket, right: WorkPacket) -> bool:
        left_axes = (
            left.value,
            left.evidence_weight,
            left.reuse_score,
            -left.estimated_seconds,
            -left.risk,
        )
        right_axes = (
            right.value,
            right.evidence_weight,
            right.reuse_score,
            -right.estimated_seconds,
            -right.risk,
        )
        return all(a >= b for a, b in zip(left_axes, right_axes)) and any(a > b for a, b in zip(left_axes, right_axes))

    return tuple(
        work_id
        for work_id in ids
        if not any(
            other != work_id and dominates(graph.packets[other], graph.packets[work_id])
            for other in ids
        )
    )
