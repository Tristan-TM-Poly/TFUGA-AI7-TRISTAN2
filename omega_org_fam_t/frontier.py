"""Adaptive, resumable frontier control with M+/M- telemetry."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

@dataclass(slots=True)
class FrontierState:
    next_index: int = 0
    batch_size: int = 4096
    completed: int = 0
    successes: int = 0
    failures: int = 0
    generation: int = 0

class AdaptiveFrontierController:
    """Controls finite runs without encoding a permanent total-object ceiling."""
    def __init__(self, *, initial_batch: int = 4096, min_batch: int = 128, growth: float = 2.0, backoff: float = 0.5):
        if initial_batch <= 0 or min_batch <= 0 or growth <= 1 or not 0 < backoff < 1:
            raise ValueError("invalid controller parameters")
        self.min_batch = min_batch
        self.growth = growth
        self.backoff = backoff
        self.state = FrontierState(batch_size=initial_batch)

    def success(self, processed: int, *, latency_s: float, memory_ratio: float) -> None:
        self.state.next_index += processed
        self.state.completed += processed
        self.state.successes += 1
        self.state.generation += 1
        if memory_ratio < 0.70 and latency_s < 60:
            self.state.batch_size = max(self.min_batch, int(self.state.batch_size * self.growth))

    def failure(self, reason: str) -> dict[str, object]:
        previous = self.state.batch_size
        self.state.failures += 1
        self.state.generation += 1
        self.state.batch_size = max(self.min_batch, int(previous * self.backoff))
        return {"generation": self.state.generation, "reason": reason, "previous_batch": previous, "next_batch": self.state.batch_size, "next_index": self.state.next_index}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self.state), indent=2)+"\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AdaptiveFrontierController":
        raw = json.loads(path.read_text(encoding="utf-8"))
        obj = cls(initial_batch=int(raw["batch_size"]))
        obj.state = FrontierState(**raw)
        return obj
