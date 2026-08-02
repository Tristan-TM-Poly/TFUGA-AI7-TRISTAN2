from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence
import uuid


@dataclass(frozen=True)
class CapacityPolicy:
    """Control policy with no permanent addition-count ceiling."""

    quality_floor: float = 0.95
    pressure_soft: float = 0.75
    pressure_hard: float = 1.0
    stable_growth: float = 2.0
    cautious_growth: float = 1.25
    minimum_batch: int = 1

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality_floor <= 1.0:
            raise ValueError("quality_floor must be between 0 and 1")
        if not 0.0 <= self.pressure_soft < self.pressure_hard:
            raise ValueError("pressure thresholds must satisfy 0 <= soft < hard")
        if self.stable_growth <= 1.0 or self.cautious_growth <= 1.0:
            raise ValueError("growth factors must be greater than 1")
        if self.minimum_batch < 1:
            raise ValueError("minimum_batch must be positive")


@dataclass(frozen=True)
class BatchResult:
    accepted: int
    rejected: int = 0
    duplicates: int = 0
    failed: int = 0
    quality_score: float = 1.0
    pressure: dict[str, float] = field(default_factory=dict)
    recoverable: bool = True
    notes: tuple[str, ...] = ()

    @property
    def peak_pressure(self) -> float:
        return max(self.pressure.values(), default=0.0)


@dataclass
class CapacityState:
    requested_batch: int
    last_safe_batch: int = 0
    largest_safe_batch: int = 0
    total_integrated: int = 0
    total_rejected: int = 0
    total_duplicates: int = 0
    saturation_count: int = 0
    iteration: int = 0


@dataclass(frozen=True)
class NegativeMemoryEvent:
    event_id: str
    timestamp: str
    iteration: int
    requested_batch: int
    last_safe_batch: int
    limiting_dimensions: tuple[str, ...]
    peak_pressure: float
    quality_score: float
    recoverable: bool
    notes: tuple[str, ...]
    status: str = "observed"


@dataclass(frozen=True)
class RunReport:
    status: str
    iterations: int
    total_integrated: int
    total_rejected: int
    total_duplicates: int
    remaining: int
    largest_safe_batch: int
    final_requested_batch: int
    saturation_count: int
    redesign_count: int
    negative_memory_events: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WorkSource(Protocol):
    @property
    def remaining(self) -> int:
        ...

    def take(self, count: int) -> list[Any]:
        ...

    def requeue_front(self, items: Sequence[Any]) -> None:
        ...


class BatchExecutor(Protocol):
    def execute(self, items: Sequence[Any]) -> BatchResult:
        ...


class RedesignableExecutor(BatchExecutor, Protocol):
    def redesign(self, event: NegativeMemoryEvent) -> bool:
        ...


class ListWorkSource:
    """Finite replayable source used by the executable R0.1 prototype."""

    def __init__(self, items: Iterable[Any]):
        self._items = deque(items)

    @property
    def remaining(self) -> int:
        return len(self._items)

    def take(self, count: int) -> list[Any]:
        if count < 1:
            raise ValueError("count must be positive")
        return [self._items.popleft() for _ in range(min(count, len(self._items)))]

    def requeue_front(self, items: Sequence[Any]) -> None:
        self._items.extendleft(reversed(items))


class MMinusLedger:
    """Append-only JSONL negative-memory ledger."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.events: list[NegativeMemoryEvent] = []

    def append(self, event: NegativeMemoryEvent) -> None:
        self.events.append(event)
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


class CheckpointWriter:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None

    def write(self, state: CapacityState, remaining: int) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {"state": asdict(state), "remaining": remaining}
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)


class AdaptiveController:
    """Capacity-seeking controller without a permanent addition-count cap.

    Termination is driven by workload exhaustion, an unrecoverable result, or a
    saturation for which no redesign is available. A saturation is recorded in
    M-minus before the affected batch is retried or the run is paused.
    """

    def __init__(
        self,
        source: WorkSource,
        executor: BatchExecutor,
        *,
        initial_batch: int = 64,
        policy: CapacityPolicy | None = None,
        ledger: MMinusLedger | None = None,
        checkpoint_path: str | Path | None = None,
    ):
        if initial_batch < 1:
            raise ValueError("initial_batch must be positive")
        self.source = source
        self.executor = executor
        self.policy = policy or CapacityPolicy()
        self.ledger = ledger or MMinusLedger()
        self.checkpoints = CheckpointWriter(checkpoint_path)
        self.state = CapacityState(requested_batch=initial_batch)
        self.redesign_count = 0

    def run(self) -> RunReport:
        status = "completed"

        while self.source.remaining:
            self.state.iteration += 1
            requested = min(self.state.requested_batch, self.source.remaining)
            items = self.source.take(requested)
            result = self.executor.execute(items)

            if self._healthy(result, requested):
                self._accept(result, requested)
                self.state.requested_batch = self._next_batch(result, requested)
                self.checkpoints.write(self.state, self.source.remaining)
                continue

            self.source.requeue_front(items)
            self.state.saturation_count += 1
            event = self._event(result, requested)
            self.ledger.append(event)
            self.checkpoints.write(self.state, self.source.remaining)

            if not result.recoverable:
                status = "paused_unrecoverable"
                break

            redesign = getattr(self.executor, "redesign", None)
            if redesign is None or not bool(redesign(event)):
                status = "paused_requires_redesign"
                break

            self.redesign_count += 1
            self.state.requested_batch = max(
                self.policy.minimum_batch,
                self.state.last_safe_batch or requested // 2 or 1,
            )

        return RunReport(
            status=status,
            iterations=self.state.iteration,
            total_integrated=self.state.total_integrated,
            total_rejected=self.state.total_rejected,
            total_duplicates=self.state.total_duplicates,
            remaining=self.source.remaining,
            largest_safe_batch=self.state.largest_safe_batch,
            final_requested_batch=self.state.requested_batch,
            saturation_count=self.state.saturation_count,
            redesign_count=self.redesign_count,
            negative_memory_events=len(self.ledger.events),
        )

    def _healthy(self, result: BatchResult, requested: int) -> bool:
        return (
            result.recoverable
            and result.failed == 0
            and result.accepted + result.rejected + result.duplicates == requested
            and result.quality_score >= self.policy.quality_floor
            and result.peak_pressure < self.policy.pressure_hard
        )

    def _accept(self, result: BatchResult, requested: int) -> None:
        self.state.last_safe_batch = requested
        self.state.largest_safe_batch = max(self.state.largest_safe_batch, requested)
        self.state.total_integrated += result.accepted
        self.state.total_rejected += result.rejected
        self.state.total_duplicates += result.duplicates

    def _next_batch(self, result: BatchResult, requested: int) -> int:
        factor = (
            self.policy.stable_growth
            if result.peak_pressure < self.policy.pressure_soft
            else self.policy.cautious_growth
        )
        return max(requested + 1, int(requested * factor))

    def _event(self, result: BatchResult, requested: int) -> NegativeMemoryEvent:
        dimensions = tuple(
            sorted(name for name, value in result.pressure.items() if value >= self.policy.pressure_hard)
        )
        if result.quality_score < self.policy.quality_floor:
            dimensions += ("quality",)
        if result.failed:
            dimensions += ("execution_failure",)
        return NegativeMemoryEvent(
            event_id=f"M-{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            iteration=self.state.iteration,
            requested_batch=requested,
            last_safe_batch=self.state.last_safe_batch,
            limiting_dimensions=tuple(dict.fromkeys(dimensions or ("unknown",))),
            peak_pressure=result.peak_pressure,
            quality_score=result.quality_score,
            recoverable=result.recoverable,
            notes=result.notes,
        )


class SyntheticCapacityExecutor:
    """Deterministic stress harness for testing frontier discovery.

    It models a temporary capacity frontier. On redesign, capacity is multiplied
    rather than hidden behind a new permanent controller cap.
    """

    def __init__(
        self,
        *,
        capacity: int = 1024,
        redesign_factor: float = 2.0,
        quality_score: float = 0.99,
        allow_redesign: bool = True,
    ):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if redesign_factor <= 1.0:
            raise ValueError("redesign_factor must be greater than 1")
        self.capacity = capacity
        self.redesign_factor = redesign_factor
        self.quality_score = quality_score
        self.allow_redesign = allow_redesign
        self.frontier_history = [capacity]

    def execute(self, items: Sequence[Any]) -> BatchResult:
        size = len(items)
        pressure = size / self.capacity
        if size > self.capacity:
            return BatchResult(
                accepted=0,
                failed=size,
                quality_score=self.quality_score,
                pressure={"synthetic_capacity": pressure},
                recoverable=True,
                notes=(f"requested {size} above observed capacity {self.capacity}",),
            )
        return BatchResult(
            accepted=size,
            quality_score=self.quality_score,
            pressure={"synthetic_capacity": pressure},
        )

    def redesign(self, event: NegativeMemoryEvent) -> bool:
        if not self.allow_redesign:
            return False
        self.capacity = max(self.capacity + 1, int(self.capacity * self.redesign_factor))
        self.frontier_history.append(self.capacity)
        return True
