from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import time
from typing import Any, Sequence
import uuid

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on some platforms
    resource = None  # type: ignore[assignment]


class RangeWorkSource:
    """Replayable lazy integer source that never materializes the full range."""

    def __init__(self, stop: int, *, start: int = 0, step: int = 1):
        if step <= 0:
            raise ValueError("step must be positive")
        if stop < start:
            raise ValueError("stop must be greater than or equal to start")
        self.start = start
        self.stop = stop
        self.step = step
        self.cursor = start
        self._replay: deque[int] = deque()

    @property
    def remaining(self) -> int:
        generated = max(0, math.ceil((self.stop - self.cursor) / self.step))
        return len(self._replay) + generated

    def take(self, count: int) -> list[int]:
        if count < 1:
            raise ValueError("count must be positive")
        items: list[int] = []
        while self._replay and len(items) < count:
            items.append(self._replay.popleft())
        while len(items) < count and self.cursor < self.stop:
            items.append(self.cursor)
            self.cursor += self.step
        return items

    def requeue_front(self, items: Sequence[Any]) -> None:
        normalized = [int(item) for item in items]
        self._replay.extendleft(reversed(normalized))

    def checkpoint(self) -> dict[str, Any]:
        return {
            "type": "range",
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
            "cursor": self.cursor,
            "replay": list(self._replay),
            "remaining": self.remaining,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "RangeWorkSource":
        source = cls(
            int(payload["stop"]),
            start=int(payload.get("start", 0)),
            step=int(payload.get("step", 1)),
        )
        source.cursor = int(payload["cursor"])
        source._replay.extend(int(item) for item in payload.get("replay", []))
        return source


@dataclass(frozen=True)
class ResourceSnapshot:
    timestamp: str
    monotonic_seconds: float
    process_cpu_seconds: float
    max_rss_kib: int | None
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    load_average_1m: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceSampler:
    """Portable best-effort telemetry with no third-party dependency."""

    def __init__(self, path: str | Path = "."):
        self.path = Path(path)

    def sample(self) -> ResourceSnapshot:
        usage = shutil.disk_usage(self.path)
        maximum_rss: int | None = None
        if resource is not None:
            maximum_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        load_average: float | None = None
        if hasattr(os, "getloadavg"):
            try:
                load_average = float(os.getloadavg()[0])
            except OSError:
                load_average = None
        return ResourceSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            monotonic_seconds=time.monotonic(),
            process_cpu_seconds=time.process_time(),
            max_rss_kib=maximum_rss,
            disk_total_bytes=usage.total,
            disk_used_bytes=usage.used,
            disk_free_bytes=usage.free,
            load_average_1m=load_average,
        )


@dataclass(frozen=True)
class BreakthroughEvent:
    event_id: str
    timestamp: str
    previous_frontier: int
    new_frontier: int
    intervention: tuple[str, ...]
    repetitions: int
    quality_before: float | None = None
    quality_after: float | None = None
    cost_before: float | None = None
    cost_after: float | None = None
    status: str = "observed_not_yet_canonized"

    @property
    def gain(self) -> float:
        if self.previous_frontier <= 0:
            return float("inf")
        return self.new_frontier / self.previous_frontier

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gain"] = self.gain
        return payload


class MPlusLedger:
    """Append-only positive memory for reproduced frontier breakthroughs."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.events: list[BreakthroughEvent] = []

    def append(self, event: BreakthroughEvent) -> None:
        if event.new_frontier <= event.previous_frontier:
            raise ValueError("new_frontier must exceed previous_frontier")
        if event.repetitions < 1:
            raise ValueError("repetitions must be positive")
        self.events.append(event)
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def record(
        self,
        *,
        previous_frontier: int,
        new_frontier: int,
        intervention: Sequence[str],
        repetitions: int,
        quality_before: float | None = None,
        quality_after: float | None = None,
        cost_before: float | None = None,
        cost_after: float | None = None,
        status: str = "observed_not_yet_canonized",
    ) -> BreakthroughEvent:
        event = BreakthroughEvent(
            event_id=f"M+{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            previous_frontier=previous_frontier,
            new_frontier=new_frontier,
            intervention=tuple(str(item) for item in intervention),
            repetitions=repetitions,
            quality_before=quality_before,
            quality_after=quality_after,
            cost_before=cost_before,
            cost_after=cost_after,
            status=status,
        )
        self.append(event)
        return event
