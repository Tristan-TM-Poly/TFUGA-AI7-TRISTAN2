from __future__ import annotations

import heapq
import json
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TemporalSignal:
    """Signals used to choose a temporal level of detail.

    Values are normalized to [0, 1]. Visibility is treated as an explicit
    causal/interactive reason to keep a system at the finest cadence.
    """

    activity: float = 0.0
    importance: float = 0.0
    uncertainty: float = 0.0
    visible: bool = False

    def normalized(self) -> "TemporalSignal":
        clamp = lambda value: max(0.0, min(1.0, float(value)))
        return TemporalSignal(
            activity=clamp(self.activity),
            importance=clamp(self.importance),
            uncertainty=clamp(self.uncertainty),
            visible=bool(self.visible),
        )

    @property
    def score(self) -> float:
        signal = self.normalized()
        return round(
            0.45 * signal.activity
            + 0.35 * signal.importance
            + 0.20 * signal.uncertainty,
            6,
        )


@dataclass(frozen=True)
class TemporalLODPolicy:
    realtime_interval: int = 1
    active_interval: int = 2
    background_interval: int = 8
    dormant_interval: int = 32
    realtime_threshold: float = 0.75
    active_threshold: float = 0.40
    background_threshold: float = 0.10

    def validate(self) -> None:
        intervals = (
            self.realtime_interval,
            self.active_interval,
            self.background_interval,
            self.dormant_interval,
        )
        if any(interval < 1 for interval in intervals):
            raise ValueError("temporal LOD intervals must be >= 1")
        if not (
            0.0 <= self.background_threshold
            <= self.active_threshold
            <= self.realtime_threshold
            <= 1.0
        ):
            raise ValueError("temporal LOD thresholds must be ordered in [0, 1]")

    def interval(self, signal: TemporalSignal | None = None) -> int:
        self.validate()
        signal = (signal or TemporalSignal()).normalized()
        if signal.visible or signal.score >= self.realtime_threshold:
            return self.realtime_interval
        if signal.score >= self.active_threshold:
            return self.active_interval
        if signal.score >= self.background_threshold:
            return self.background_interval
        return self.dormant_interval


@dataclass(frozen=True)
class SystemSpec:
    system_id: str
    priority: int = 0
    max_batch: int = 1024
    cost_per_entity: float = 1.0
    cost_per_event: float = 0.25
    wake_on_dirty: bool = True
    wake_on_event: bool = True

    def validate(self) -> None:
        if not self.system_id:
            raise ValueError("system_id cannot be empty")
        if self.max_batch < 1:
            raise ValueError("max_batch must be >= 1")
        if self.cost_per_entity < 0 or self.cost_per_event < 0:
            raise ValueError("cost coefficients must be non-negative")


@dataclass(frozen=True)
class ScheduledEvent:
    tick: int
    event_id: str
    system_id: str
    entity_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.tick < 0:
            raise ValueError("event tick must be >= 0")
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if not self.system_id:
            raise ValueError("system_id cannot be empty")


@dataclass
class DirtyFrontier:
    """Deterministic set-like frontier of entities requiring recomputation."""

    _items: set[str] = field(default_factory=set)

    def mark(self, entity_id: str) -> None:
        if not entity_id:
            raise ValueError("entity_id cannot be empty")
        self._items.add(entity_id)

    def mark_many(self, entity_ids: Iterable[str]) -> None:
        for entity_id in entity_ids:
            self.mark(entity_id)

    def consume(self, limit: int) -> tuple[str, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        selected = tuple(sorted(self._items)[:limit])
        self._items.difference_update(selected)
        return selected

    def snapshot(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class Dispatch:
    tick: int
    system_id: str
    entity_ids: tuple[str, ...]
    events: tuple[ScheduledEvent, ...]
    interval: int
    reasons: tuple[str, ...]
    estimated_work: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "system_id": self.system_id,
            "entity_ids": list(self.entity_ids),
            "events": [asdict(event) for event in self.events],
            "interval": self.interval,
            "reasons": list(self.reasons),
            "estimated_work": self.estimated_work,
        }


@dataclass(frozen=True)
class SchedulerTickReport:
    tick: int
    dispatches: tuple[Dispatch, ...]
    skipped_systems: tuple[str, ...]

    @property
    def estimated_work(self) -> float:
        return round(sum(dispatch.estimated_work for dispatch in self.dispatches), 6)

    @property
    def processed_entities(self) -> int:
        return sum(len(dispatch.entity_ids) for dispatch in self.dispatches)

    @property
    def processed_events(self) -> int:
        return sum(len(dispatch.events) for dispatch in self.dispatches)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "dispatches": [dispatch.to_dict() for dispatch in self.dispatches],
            "skipped_systems": list(self.skipped_systems),
            "estimated_work": self.estimated_work,
            "processed_entities": self.processed_entities,
            "processed_events": self.processed_events,
        }


@dataclass
class CostNode:
    invocations: int = 0
    processed_entities: int = 0
    processed_events: int = 0
    estimated_work: float = 0.0

    def to_dict(self) -> dict[str, int | float]:
        return {
            "invocations": self.invocations,
            "processed_entities": self.processed_entities,
            "processed_events": self.processed_events,
            "estimated_work": round(self.estimated_work, 6),
        }


@dataclass
class CostGraph:
    """Deterministic accounting graph for scheduler work units.

    This is not a wall-clock profiler. Work units make algorithmic comparisons
    reproducible before hardware-specific profiling is introduced.
    """

    nodes: dict[str, CostNode] = field(default_factory=dict)

    def observe(self, report: SchedulerTickReport) -> None:
        for dispatch in report.dispatches:
            node = self.nodes.setdefault(dispatch.system_id, CostNode())
            node.invocations += 1
            node.processed_entities += len(dispatch.entity_ids)
            node.processed_events += len(dispatch.events)
            node.estimated_work += dispatch.estimated_work

    @property
    def estimated_work(self) -> float:
        return round(sum(node.estimated_work for node in self.nodes.values()), 6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "systems": {system_id: self.nodes[system_id].to_dict() for system_id in sorted(self.nodes)},
            "estimated_work": self.estimated_work,
        }


class SparseEventScheduler:
    """Deterministic sparse/event-driven scheduler with Temporal LOD.

    Dirty entities and due events form the active causal frontier. Systems with
    no pending work are skipped even when their timer is due. Events can wake a
    dormant system immediately, while systems may opt out of dirty/event wakeups
    to respect a coarser temporal cadence.
    """

    def __init__(self, policy: TemporalLODPolicy | None = None) -> None:
        self.policy = policy or TemporalLODPolicy()
        self.policy.validate()
        self._specs: dict[str, SystemSpec] = {}
        self._frontiers: dict[str, DirtyFrontier] = {}
        self._next_due: dict[str, int] = {}
        self._event_heap: list[tuple[int, int, ScheduledEvent]] = []
        self._ready_events: dict[str, list[ScheduledEvent]] = {}
        self._sequence = 0

    def register(self, spec: SystemSpec) -> None:
        spec.validate()
        if spec.system_id in self._specs:
            raise ValueError(f"duplicate system_id: {spec.system_id}")
        self._specs[spec.system_id] = spec
        self._frontiers[spec.system_id] = DirtyFrontier()
        self._ready_events[spec.system_id] = []
        self._next_due[spec.system_id] = 0

    def mark_dirty(self, system_id: str, entity_id: str) -> None:
        self._require_system(system_id)
        self._frontiers[system_id].mark(entity_id)

    def mark_many(self, system_id: str, entity_ids: Iterable[str]) -> None:
        self._require_system(system_id)
        self._frontiers[system_id].mark_many(entity_ids)

    def schedule_event(self, event: ScheduledEvent) -> None:
        event.validate()
        self._require_system(event.system_id)
        self._sequence += 1
        heapq.heappush(self._event_heap, (event.tick, self._sequence, event))

    def pending_dirty(self, system_id: str) -> tuple[str, ...]:
        self._require_system(system_id)
        return self._frontiers[system_id].snapshot()

    def next_due(self, system_id: str) -> int:
        self._require_system(system_id)
        return self._next_due[system_id]

    @property
    def pending_event_count(self) -> int:
        return len(self._event_heap) + sum(len(events) for events in self._ready_events.values())

    def dispatch_tick(
        self,
        tick: int,
        *,
        signals: Mapping[str, TemporalSignal] | None = None,
    ) -> SchedulerTickReport:
        if tick < 0:
            raise ValueError("tick must be >= 0")
        signals = signals or {}
        self._activate_events(tick)
        dispatches: list[Dispatch] = []
        skipped: list[str] = []

        ordered_specs = sorted(self._specs.values(), key=lambda spec: (-spec.priority, spec.system_id))
        for spec in ordered_specs:
            system_id = spec.system_id
            frontier = self._frontiers[system_id]
            ready_events = self._ready_events[system_id]
            signal = signals.get(system_id, TemporalSignal())
            interval = self.policy.interval(signal)
            time_due = tick >= self._next_due[system_id]
            dirty_wake = bool(frontier) and spec.wake_on_dirty
            event_wake = bool(ready_events) and spec.wake_on_event
            has_work = bool(frontier) or bool(ready_events)

            if not has_work or not (time_due or dirty_wake or event_wake):
                skipped.append(system_id)
                continue

            reasons: list[str] = []
            if time_due:
                reasons.append("timer")
            if dirty_wake:
                reasons.append("dirty")
            if event_wake:
                reasons.append("event")

            entity_ids = frontier.consume(spec.max_batch) if frontier else ()
            events = tuple(ready_events)
            ready_events.clear()
            estimated_work = round(
                len(entity_ids) * spec.cost_per_entity + len(events) * spec.cost_per_event,
                6,
            )
            dispatches.append(
                Dispatch(
                    tick=tick,
                    system_id=system_id,
                    entity_ids=entity_ids,
                    events=events,
                    interval=interval,
                    reasons=tuple(reasons),
                    estimated_work=estimated_work,
                )
            )
            self._next_due[system_id] = tick + interval

        return SchedulerTickReport(
            tick=tick,
            dispatches=tuple(dispatches),
            skipped_systems=tuple(skipped),
        )

    def _activate_events(self, tick: int) -> None:
        while self._event_heap and self._event_heap[0][0] <= tick:
            _, _, event = heapq.heappop(self._event_heap)
            self._ready_events[event.system_id].append(event)
            if event.entity_id:
                self._frontiers[event.system_id].mark(event.entity_id)

    def _require_system(self, system_id: str) -> None:
        if system_id not in self._specs:
            raise KeyError(f"unknown system_id: {system_id}")


@dataclass(frozen=True)
class SparseBenchmarkReport:
    entity_count: int
    active_entities: int
    ticks: int
    naive_work_units: float
    sparse_work_units: float
    reduction_ratio: float
    dispatch_count: int
    cost_graph: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def run_sparse_benchmark(
    *,
    entity_count: int = 10_000,
    active_entities: int = 100,
    ticks: int = 128,
    seed: int = 0,
) -> SparseBenchmarkReport:
    """Compare deterministic work units for full-scan vs sparse scheduling.

    The report is an algorithmic accounting benchmark, not a hardware speed
    benchmark. Each entity update costs one work unit in both baselines.
    """

    if entity_count < 1:
        raise ValueError("entity_count must be >= 1")
    if not 0 <= active_entities <= entity_count:
        raise ValueError("active_entities must be in [0, entity_count]")
    if ticks < 1:
        raise ValueError("ticks must be >= 1")

    scheduler = SparseEventScheduler()
    scheduler.register(SystemSpec("agents", max_batch=max(1, entity_count), cost_per_entity=1.0))
    rng = random.Random(int(seed))
    population = [f"entity_{index:08d}" for index in range(entity_count)]
    active = tuple(sorted(rng.sample(population, k=active_entities))) if active_entities else ()
    cost = CostGraph()
    dispatch_count = 0

    for tick in range(ticks):
        scheduler.mark_many("agents", active)
        report = scheduler.dispatch_tick(
            tick,
            signals={"agents": TemporalSignal(activity=1.0, importance=1.0, visible=True)},
        )
        cost.observe(report)
        dispatch_count += len(report.dispatches)

    naive_work = float(entity_count * ticks)
    sparse_work = cost.estimated_work
    reduction = 0.0 if naive_work == 0 else 1.0 - sparse_work / naive_work
    return SparseBenchmarkReport(
        entity_count=entity_count,
        active_entities=active_entities,
        ticks=ticks,
        naive_work_units=naive_work,
        sparse_work_units=sparse_work,
        reduction_ratio=round(reduction, 6),
        dispatch_count=dispatch_count,
        cost_graph=cost.to_dict(),
    )
