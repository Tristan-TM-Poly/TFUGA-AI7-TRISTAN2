from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Iterable, Iterator, Mapping
import json
import math
import os


@dataclass
class FrontierBudget:
    max_seconds: float | None = None
    max_bytes: int | None = None
    max_failures: int | None = None
    target_quality: float = 0.95
    initial_batch: int = 256
    min_batch: int = 1
    max_batch_by_resource: int | None = None
    growth_factor: float = 2.0
    shrink_factor: float = 0.5

    def validate(self) -> None:
        if self.max_seconds is not None and self.max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        if self.max_bytes is not None and self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if self.max_failures is not None and self.max_failures < 0:
            raise ValueError("max_failures cannot be negative")
        if not 0 <= self.target_quality <= 1:
            raise ValueError("target_quality must be in [0, 1]")
        if self.initial_batch < 1 or self.min_batch < 1:
            raise ValueError("batch sizes must be positive")
        if self.growth_factor <= 1:
            raise ValueError("growth_factor must exceed 1")
        if not 0 < self.shrink_factor < 1:
            raise ValueError("shrink_factor must lie in (0, 1)")


@dataclass
class FrontierCheckpoint:
    processed: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    failures: int = 0
    bytes_written: int = 0
    batch_size: int = 0
    elapsed_seconds: float = 0.0
    stop_reason: str = ""
    source_exhausted: bool = False
    frontier_digest: str = ""
    m_minus: list[dict[str, Any]] = field(default_factory=list)


class AdaptiveFrontier:
    """Resource-bounded streaming engine without a permanent item-count ceiling.

    The source may be finite or unbounded. Each run is bounded by physical or
    governance budgets. No `max_items` constant is embedded in the controller.
    """

    def __init__(self, budget: FrontierBudget) -> None:
        budget.validate()
        self.budget = budget

    def run(
        self,
        source: Iterable[Mapping[str, Any]],
        output_jsonl: str | Path,
        validator: Callable[[Mapping[str, Any]], tuple[bool, float, str]],
        key: Callable[[Mapping[str, Any]], str],
        checkpoint_path: str | Path | None = None,
    ) -> FrontierCheckpoint:
        output = Path(output_jsonl)
        output.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file = Path(checkpoint_path) if checkpoint_path else output.with_suffix(output.suffix + ".checkpoint.json")
        state = FrontierCheckpoint(batch_size=self.budget.initial_batch)
        start = perf_counter()
        seen: set[str] = set()
        rolling = sha256()
        iterator = iter(source)
        exhausted = False
        with output.open("w", encoding="utf-8") as handle:
            while not exhausted:
                stop = self._stop_reason(state, start)
                if stop:
                    state.stop_reason = stop
                    break
                batch: list[Mapping[str, Any]] = []
                for _ in range(state.batch_size):
                    try:
                        batch.append(next(iterator))
                    except StopIteration:
                        exhausted = True
                        state.source_exhausted = True
                        break
                if not batch:
                    break
                accepted_this_batch = 0
                failures_before = state.failures
                for item in batch:
                    state.processed += 1
                    try:
                        identity = key(item)
                        if identity in seen:
                            state.duplicates += 1
                            continue
                        seen.add(identity)
                        passed, quality, reason = validator(item)
                        if not passed or quality < self.budget.target_quality:
                            state.rejected += 1
                            state.m_minus.append({"key": identity, "quality": quality, "reason": reason, "processed": state.processed})
                            continue
                        canonical = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        line = canonical + "\n"
                        encoded = line.encode("utf-8")
                        if self.budget.max_bytes is not None and state.bytes_written + len(encoded) > self.budget.max_bytes:
                            state.stop_reason = "byte_budget"
                            exhausted = True
                            break
                        handle.write(line)
                        rolling.update(encoded)
                        state.bytes_written += len(encoded)
                        state.accepted += 1
                        accepted_this_batch += 1
                    except Exception as exc:
                        state.failures += 1
                        state.m_minus.append({"reason": "exception", "error": repr(exc), "processed": state.processed})
                quality_ratio = accepted_this_batch / max(1, len(batch))
                new_failures = state.failures - failures_before
                state.batch_size = self._next_batch(state.batch_size, quality_ratio, new_failures)
                state.elapsed_seconds = perf_counter() - start
                state.frontier_digest = rolling.hexdigest()
                checkpoint_file.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        state.elapsed_seconds = perf_counter() - start
        state.frontier_digest = rolling.hexdigest()
        if not state.stop_reason:
            state.stop_reason = "source_exhausted" if state.source_exhausted else "completed"
        checkpoint_file.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return state

    def _next_batch(self, current: int, quality_ratio: float, failures: int) -> int:
        if failures > 0 or quality_ratio < self.budget.target_quality:
            candidate = max(self.budget.min_batch, int(math.floor(current * self.budget.shrink_factor)))
        else:
            candidate = max(self.budget.min_batch, int(math.ceil(current * self.budget.growth_factor)))
        if self.budget.max_batch_by_resource is not None:
            candidate = min(candidate, self.budget.max_batch_by_resource)
        return candidate

    def _stop_reason(self, state: FrontierCheckpoint, start: float) -> str:
        if self.budget.max_seconds is not None and perf_counter() - start >= self.budget.max_seconds:
            return "time_budget"
        if self.budget.max_bytes is not None and state.bytes_written >= self.budget.max_bytes:
            return "byte_budget"
        if self.budget.max_failures is not None and state.failures >= self.budget.max_failures:
            return "failure_budget"
        return ""


def synthetic_particle_candidates(namespaces: int = 16):
    index = 0
    while True:
        namespace = index % max(1, namespaces)
        yield {
            "id": f"candidate::{namespace:04d}::{index:020d}",
            "namespace": namespace,
            "ordinal": index,
            "status": "hypothesis",
            "ontology_level": "hypothetical",
            "claim": "Synthetic capacity-frontier object; not a physical discovery.",
            "provenance": "omega_pct_t.frontier.synthetic_particle_candidates",
            "falsifier": "Fails schema, duplication, resource, or quality gate.",
        }
        index += 1
