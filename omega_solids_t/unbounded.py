from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol

from .atlas import ARCHETYPE_NAMES, build_archetype, clone_with_identifier
from .genome import SolidGenome
from .invariants import build_signature
from .oak import run_oak_gate


class GenomeSink(Protocol):
    def write(self, genome: SolidGenome, metadata: Mapping[str, Any]) -> None: ...
    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class FrontierPolicy:
    initial_batch: int = 128
    growth_factor: float = 2.0
    shrink_factor: float = 0.5
    quality_floor: float = 0.70
    latency_target_s: float = 1.0
    checkpoint_every_batches: int = 1
    memory_budget_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.initial_batch <= 0:
            raise ValueError("Initial batch must be positive")
        if self.growth_factor <= 1:
            raise ValueError("Growth factor must exceed one")
        if not 0 < self.shrink_factor < 1:
            raise ValueError("Shrink factor must be within (0, 1)")
        if not 0 <= self.quality_floor <= 1:
            raise ValueError("Quality floor must be within [0, 1]")
        if self.latency_target_s <= 0:
            raise ValueError("Latency target must be positive")
        if self.checkpoint_every_batches <= 0:
            raise ValueError("Checkpoint interval must be positive")
        if self.memory_budget_bytes is not None and self.memory_budget_bytes <= 0:
            raise ValueError("Memory budget must be positive")


@dataclass(frozen=True, slots=True)
class FrontierEvent:
    sequence: int
    event: str
    batch_size: int
    processed: int
    accepted: int
    quality: float
    elapsed_s: float
    detail: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event": self.event,
            "batch_size": self.batch_size,
            "processed": self.processed,
            "accepted": self.accepted,
            "quality": self.quality,
            "elapsed_s": self.elapsed_s,
            "detail": dict(self.detail),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class JSONLGenomeSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def write(self, genome: SolidGenome, metadata: Mapping[str, Any]) -> None:
        payload = {"genome": genome.to_dict(), "metadata": dict(metadata)}
        self._handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class DedupLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._hashes: set[str] = set()
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._hashes.add(line.strip())

    def accept(self, genome: SolidGenome) -> bool:
        fingerprint = genome.fingerprint()
        if fingerprint in self._hashes:
            return False
        self._hashes.add(fingerprint)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(fingerprint + "\n")
        return True

    def __len__(self) -> int:
        return len(self._hashes)


class ArchetypeMutationSource:
    """Lazy deterministic source with no built-in total-count ceiling.

    The caller supplies a finite experiment budget, deadline, or external stop
    condition. The source itself can continue generating identifiers and
    controlled geometry/process mutations without materializing all candidates.
    """

    def __init__(self, start: int = 0) -> None:
        if start < 0:
            raise ValueError("Start cannot be negative")
        self.position = start

    def __iter__(self) -> "ArchetypeMutationSource":
        return self

    def __next__(self) -> SolidGenome:
        return self.candidate()

    def candidate(self) -> SolidGenome:
        """Generate a candidate while preserving dataclass types.

        This separate method avoids mapping round-trips in the hot path.
        """
        from dataclasses import replace

        index = self.position
        self.position += 1
        archetype_name = ARCHETYPE_NAMES[index % len(ARCHETYPE_NAMES)]
        epoch = index // len(ARCHETYPE_NAMES)
        genome = build_archetype(archetype_name)
        geometry = dict(genome.geometry)
        geometry["generator_epoch"] = epoch
        geometry["controlled_scale_factor"] = 1.0 + ((epoch % 101) - 50) / 1000.0
        process = (*genome.process, {"name": "generated_variant", "epoch": epoch})
        return replace(
            genome,
            identifier=f"generated-{archetype_name}-{epoch:012d}",
            name=f"{genome.name} variant {epoch}",
            geometry=geometry,
            process=process,
        )


def iter_candidates(source: ArchetypeMutationSource) -> Iterator[SolidGenome]:
    while True:
        yield source.candidate()


@dataclass(frozen=True, slots=True)
class FrontierReport:
    requested: int | None
    processed: int
    accepted: int
    duplicates: int
    rejected_quality: int
    batches: int
    final_batch_size: int
    status: str
    events: tuple[FrontierEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "processed": self.processed,
            "accepted": self.accepted,
            "duplicates": self.duplicates,
            "rejected_quality": self.rejected_quality,
            "batches": self.batches,
            "final_batch_size": self.final_batch_size,
            "status": self.status,
            "events": [event.to_dict() for event in self.events],
            "boundary": (
                "No permanent total-addition ceiling is encoded. This report is bounded by the "
                "explicit finite work target or stop predicate, quality floor, storage, compute, "
                "rollback, provider and safety constraints."
            ),
        }


class AdaptiveSolidFrontier:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        policy: FrontierPolicy = FrontierPolicy(),
        quality_function: Callable[[SolidGenome], float] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.policy = policy
        self.quality_function = quality_function or (
            lambda genome: run_oak_gate(genome).score
        )
        self.checkpoint_path = self.output_dir / "checkpoint.json"
        self.events_path = self.output_dir / "frontier-events.jsonl"
        self.m_minus_path = self.output_dir / "m_minus.jsonl"
        self.m_plus_path = self.output_dir / "m_plus.jsonl"
        self.dedup = DedupLedger(self.output_dir / "fingerprints.txt")

    def _append_event(self, event: FrontierEvent) -> None:
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def _append_ledger(self, path: Path, payload: Mapping[str, Any]) -> None:
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), **dict(payload)}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def _write_checkpoint(self, payload: Mapping[str, Any]) -> None:
        temporary = self.checkpoint_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.checkpoint_path)

    def run(
        self,
        source: ArchetypeMutationSource,
        *,
        sink: GenomeSink,
        work_items: int | None,
        stop_predicate: Callable[[Mapping[str, int]], bool] | None = None,
    ) -> FrontierReport:
        if work_items is None and stop_predicate is None:
            raise ValueError("Provide a finite work_items target or an external stop predicate")
        if work_items is not None and work_items < 0:
            raise ValueError("work_items cannot be negative")
        batch_size = self.policy.initial_batch
        processed = accepted = duplicates = rejected_quality = batches = 0
        events: list[FrontierEvent] = []
        iterator = iter_candidates(source)
        try:
            while work_items is None or processed < work_items:
                counters = {
                    "processed": processed,
                    "accepted": accepted,
                    "duplicates": duplicates,
                    "rejected_quality": rejected_quality,
                    "batches": batches,
                }
                if stop_predicate is not None and stop_predicate(counters):
                    break
                actual_batch = (
                    batch_size
                    if work_items is None
                    else min(batch_size, work_items - processed)
                )
                if actual_batch <= 0:
                    break
                started = time.perf_counter()
                batch_accepted = 0
                quality_values: list[float] = []
                for _ in range(actual_batch):
                    genome = next(iterator)
                    processed += 1
                    if not self.dedup.accept(genome):
                        duplicates += 1
                        continue
                    quality = float(self.quality_function(genome))
                    quality_values.append(quality)
                    if quality < self.policy.quality_floor:
                        rejected_quality += 1
                        self._append_ledger(
                            self.m_minus_path,
                            {
                                "type": "quality_rejection",
                                "genome_id": genome.identifier,
                                "quality": quality,
                                "quality_floor": self.policy.quality_floor,
                                "action": "improve provenance, uncertainty, baseline or stability evidence",
                            },
                        )
                        continue
                    signature = build_signature(genome)
                    sink.write(
                        genome,
                        {
                            "quality": quality,
                            "cvcd_signature": signature.to_dict(),
                            "source_position": source.position,
                        },
                    )
                    accepted += 1
                    batch_accepted += 1
                elapsed = time.perf_counter() - started
                batches += 1
                mean_quality = (
                    sum(quality_values) / len(quality_values) if quality_values else 0.0
                )
                acceptance_rate = batch_accepted / actual_batch
                previous_batch = batch_size
                event_type = "frontier_hold"
                if (
                    elapsed <= self.policy.latency_target_s
                    and mean_quality >= self.policy.quality_floor
                    and acceptance_rate >= 0.8
                ):
                    batch_size = max(batch_size + 1, math.ceil(batch_size * self.policy.growth_factor))
                    event_type = "frontier_expand"
                    self._append_ledger(
                        self.m_plus_path,
                        {
                            "type": "capacity_expansion",
                            "from_batch": previous_batch,
                            "to_batch": batch_size,
                            "elapsed_s": elapsed,
                            "mean_quality": mean_quality,
                            "acceptance_rate": acceptance_rate,
                            "status": "single_run_observation_not_canonized",
                        },
                    )
                elif elapsed > self.policy.latency_target_s * 2 or mean_quality < self.policy.quality_floor:
                    batch_size = max(1, math.floor(batch_size * self.policy.shrink_factor))
                    event_type = "frontier_backpressure"
                    self._append_ledger(
                        self.m_minus_path,
                        {
                            "type": "capacity_saturation",
                            "from_batch": previous_batch,
                            "to_batch": batch_size,
                            "elapsed_s": elapsed,
                            "mean_quality": mean_quality,
                            "acceptance_rate": acceptance_rate,
                            "redesign_candidates": [
                                "increase shard count",
                                "use disk-backed indexing",
                                "parallelize independent OAK gates",
                                "cache invariant computations",
                                "reduce serialization overhead",
                            ],
                        },
                    )
                event = FrontierEvent(
                    batches,
                    event_type,
                    previous_batch,
                    processed,
                    accepted,
                    mean_quality,
                    elapsed,
                    {
                        "next_batch_size": batch_size,
                        "acceptance_rate": acceptance_rate,
                        "actual_batch": actual_batch,
                    },
                )
                events.append(event)
                self._append_event(event)
                if batches % self.policy.checkpoint_every_batches == 0:
                    self._write_checkpoint(
                        {
                            "source_position": source.position,
                            "processed": processed,
                            "accepted": accepted,
                            "duplicates": duplicates,
                            "rejected_quality": rejected_quality,
                            "batches": batches,
                            "next_batch_size": batch_size,
                        }
                    )
        finally:
            sink.close()
        status = "completed" if work_items is not None and processed >= work_items else "stopped"
        report = FrontierReport(
            work_items,
            processed,
            accepted,
            duplicates,
            rejected_quality,
            batches,
            batch_size,
            status,
            tuple(events),
        )
        (self.output_dir / "frontier-report.json").write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report
