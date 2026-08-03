"""Deterministic distributed execution plans for the R∞ logical cell space.

The module partitions finite campaign slices without materializing the full
34,359,738,368-cell address space.  It produces mergeable receipts, detects
duplicate work and preserves deterministic order independently of worker count.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from math import ceil
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .address import CellSpace, FeistelPermutation
from .models import CellAddress


class WorkStatus(str, Enum):
    PLANNED = "planned"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ShardSpec:
    shard_id: str
    shard_index: int
    shard_count: int
    seed: int
    start_rank: int
    stop_rank: int
    stride: int = 1
    logical_cells: int = 34_359_738_368

    def __post_init__(self) -> None:
        if self.shard_count <= 0:
            raise ValueError("shard_count must be positive")
        if not 0 <= self.shard_index < self.shard_count:
            raise ValueError("shard_index outside range")
        if self.start_rank < 0 or self.stop_rank < self.start_rank:
            raise ValueError("invalid rank interval")
        if self.stop_rank > self.logical_cells:
            raise ValueError("rank interval exceeds logical space")
        if self.stride <= 0:
            raise ValueError("stride must be positive")

    @property
    def planned_cells(self) -> int:
        if self.stop_rank <= self.start_rank:
            return 0
        return ceil((self.stop_rank - self.start_rank) / self.stride)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WorkUnit:
    work_id: str
    campaign_id: str
    shard_id: str
    sequence_number: int
    rank: int
    flat_index: int
    address: CellAddress
    estimated_compute: float
    estimated_storage_bytes: int
    priority: float
    dependency_ids: tuple[str, ...] = ()
    status: WorkStatus = WorkStatus.PLANNED

    def __post_init__(self) -> None:
        if self.sequence_number < 0 or self.rank < 0 or self.flat_index < 0:
            raise ValueError("work indices must be non-negative")
        if self.estimated_compute < 0 or self.estimated_storage_bytes < 0:
            raise ValueError("resource estimates must be non-negative")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["address"] = self.address.render()
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class WorkResult:
    work_id: str
    worker_id: str
    status: WorkStatus
    input_digest: str
    output_digest: str | None
    evidence_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    counterexample_ids: tuple[str, ...]
    failure_codes: tuple[str, ...]
    compute_spent: float
    storage_bytes: int
    attempt: int = 1

    def __post_init__(self) -> None:
        if self.status not in {WorkStatus.COMPLETED, WorkStatus.FAILED, WorkStatus.DEFERRED, WorkStatus.CANCELLED}:
            raise ValueError("result requires a terminal status")
        if self.compute_spent < 0 or self.storage_bytes < 0 or self.attempt <= 0:
            raise ValueError("invalid result accounting")
        if self.status == WorkStatus.COMPLETED and self.output_digest is None:
            raise ValueError("completed result requires output digest")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class WorkerManifest:
    worker_id: str
    implementation_digest: str
    environment_digest: str
    supported_families: tuple[int, ...]
    supported_transformations: tuple[int, ...]
    maximum_concurrency: int
    memory_megabytes: int
    exact_arithmetic: bool

    def __post_init__(self) -> None:
        if len(self.implementation_digest) != 64 or len(self.environment_digest) != 64:
            raise ValueError("worker digests must be SHA-256 length")
        if self.maximum_concurrency <= 0 or self.memory_megabytes <= 0:
            raise ValueError("worker resources must be positive")

    def supports(self, address: CellAddress) -> bool:
        return (
            (not self.supported_families or address.family in self.supported_families)
            and (not self.supported_transformations or address.transformation in self.supported_transformations)
        )


@dataclass
class WorkLedger:
    campaign_id: str
    planned: dict[str, WorkUnit] = field(default_factory=dict)
    results: dict[str, list[WorkResult]] = field(default_factory=dict)

    def add_work(self, unit: WorkUnit) -> None:
        existing = self.planned.get(unit.work_id)
        if existing is not None and existing != unit:
            raise ValueError(f"work ID collision: {unit.work_id}")
        if unit.campaign_id != self.campaign_id:
            raise ValueError("campaign mismatch")
        self.planned[unit.work_id] = unit

    def add_result(self, result: WorkResult) -> None:
        if result.work_id not in self.planned:
            raise KeyError(f"unknown work ID: {result.work_id}")
        attempts = self.results.setdefault(result.work_id, [])
        if any(item.attempt == result.attempt for item in attempts):
            raise ValueError("duplicate work attempt")
        attempts.append(result)
        attempts.sort(key=lambda item: item.attempt)

    def terminal_result(self, work_id: str) -> WorkResult | None:
        attempts = self.results.get(work_id, [])
        completed = [item for item in attempts if item.status == WorkStatus.COMPLETED]
        if completed:
            return completed[-1]
        return attempts[-1] if attempts else None

    def unresolved_work(self) -> tuple[WorkUnit, ...]:
        return tuple(
            unit
            for work_id, unit in sorted(self.planned.items())
            if self.terminal_result(work_id) is None
            or self.terminal_result(work_id).status not in {WorkStatus.COMPLETED, WorkStatus.CANCELLED}
        )

    def validate(self) -> list[str]:
        errors = []
        seen_flat: dict[int, str] = {}
        seen_address: dict[CellAddress, str] = {}
        for work_id, unit in self.planned.items():
            if unit.flat_index in seen_flat and seen_flat[unit.flat_index] != work_id:
                errors.append(f"duplicate flat index {unit.flat_index}: {seen_flat[unit.flat_index]} and {work_id}")
            seen_flat[unit.flat_index] = work_id
            if unit.address in seen_address and seen_address[unit.address] != work_id:
                errors.append(f"duplicate address {unit.address.render()}")
            seen_address[unit.address] = work_id
            missing = [dependency for dependency in unit.dependency_ids if dependency not in self.planned]
            if missing:
                errors.append(f"{work_id}: missing dependencies {missing}")
        for work_id, attempts in self.results.items():
            if work_id not in self.planned:
                errors.append(f"orphan results for {work_id}")
            completed_digests = {
                item.output_digest
                for item in attempts
                if item.status == WorkStatus.COMPLETED
            }
            if len(completed_digests) > 1:
                errors.append(f"nondeterministic completed outputs for {work_id}")
        return errors

    def receipt(self) -> dict[str, object]:
        terminal = [self.terminal_result(work_id) for work_id in self.planned]
        completed = [item for item in terminal if item is not None and item.status == WorkStatus.COMPLETED]
        failed = [item for item in terminal if item is not None and item.status == WorkStatus.FAILED]
        payload = {
            "schema": "omega-distributed-work-ledger/1",
            "campaign_id": self.campaign_id,
            "planned_work": len(self.planned),
            "completed_work": len(completed),
            "failed_work": len(failed),
            "unresolved_work": len(self.unresolved_work()),
            "compute_spent": sum(item.compute_spent for item in completed + failed),
            "storage_bytes": sum(item.storage_bytes for item in completed + failed),
            "candidate_count": sum(len(item.candidate_ids) for item in completed),
            "counterexample_count": sum(len(item.counterexample_ids) for item in completed),
            "validation_errors": self.validate(),
            "permanent_total_cap": None,
            "global_identity_proved": False,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["ledger_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


EstimateFunction = Callable[[CellAddress], tuple[float, int, float]]


def deterministic_estimate(address: CellAddress) -> tuple[float, int, float]:
    digest = sha256(address.render().encode("ascii")).digest()
    compute = 0.1 + int.from_bytes(digest[:2], "big") / 8192
    storage = 128 + int.from_bytes(digest[2:6], "big") % 1_000_000
    priority = int.from_bytes(digest[6:10], "big") / 2**32
    return compute, storage, priority


def partition_ranks(total_ranks: int, shard_count: int, *, seed: int = 0) -> tuple[ShardSpec, ...]:
    if total_ranks < 0 or shard_count <= 0:
        raise ValueError("invalid partition dimensions")
    width = ceil(total_ranks / shard_count) if total_ranks else 0
    shards = []
    for index in range(shard_count):
        start = min(total_ranks, index * width)
        stop = min(total_ranks, start + width)
        shards.append(
            ShardSpec(
                shard_id=f"shard.{index:05d}-of-{shard_count:05d}",
                shard_index=index,
                shard_count=shard_count,
                seed=seed,
                start_rank=start,
                stop_rank=stop,
            )
        )
    return tuple(shards)


def strided_shards(total_ranks: int, shard_count: int, *, seed: int = 0) -> tuple[ShardSpec, ...]:
    if total_ranks < 0 or shard_count <= 0:
        raise ValueError("invalid shard dimensions")
    return tuple(
        ShardSpec(
            shard_id=f"stride.{index:05d}-of-{shard_count:05d}",
            shard_index=index,
            shard_count=shard_count,
            seed=seed,
            start_rank=index,
            stop_rank=total_ranks,
            stride=shard_count,
        )
        for index in range(shard_count)
    )


def iter_shard_work(
    shard: ShardSpec,
    *,
    campaign_id: str,
    space: CellSpace | None = None,
    estimator: EstimateFunction = deterministic_estimate,
) -> Iterator[WorkUnit]:
    space = space or CellSpace()
    if shard.logical_cells != space.logical_cells:
        raise ValueError("shard logical size differs from cell space")
    permutation = FeistelPermutation(space.logical_cells, seed=shard.seed)
    sequence = 0
    for rank in range(shard.start_rank, shard.stop_rank, shard.stride):
        flat = permutation.permute(rank)
        address = space.unflatten(flat)
        compute, storage, priority = estimator(address)
        canonical = f"{campaign_id}:{shard.shard_id}:{rank}:{flat}:{address.render()}"
        work_id = "work." + sha256(canonical.encode("ascii")).hexdigest()[:24]
        yield WorkUnit(
            work_id=work_id,
            campaign_id=campaign_id,
            shard_id=shard.shard_id,
            sequence_number=sequence,
            rank=rank,
            flat_index=flat,
            address=address,
            estimated_compute=compute,
            estimated_storage_bytes=storage,
            priority=priority,
        )
        sequence += 1


def assign_work(
    units: Iterable[WorkUnit],
    workers: Sequence[WorkerManifest],
) -> dict[str, tuple[WorkUnit, ...]]:
    if not workers:
        raise ValueError("at least one worker is required")
    assignments: dict[str, list[WorkUnit]] = {worker.worker_id: [] for worker in workers}
    load: dict[str, float] = {worker.worker_id: 0.0 for worker in workers}
    for unit in sorted(units, key=lambda item: (-item.priority, item.rank, item.work_id)):
        eligible = [worker for worker in workers if worker.supports(unit.address)]
        if not eligible:
            continue
        worker = min(
            eligible,
            key=lambda item: (
                load[item.worker_id] / item.maximum_concurrency,
                item.worker_id,
            ),
        )
        assignments[worker.worker_id].append(unit)
        load[worker.worker_id] += unit.estimated_compute
    return {worker_id: tuple(items) for worker_id, items in assignments.items()}


def merge_ledgers(campaign_id: str, ledgers: Sequence[WorkLedger]) -> WorkLedger:
    merged = WorkLedger(campaign_id)
    for ledger in sorted(ledgers, key=lambda item: item.campaign_id):
        if ledger.campaign_id != campaign_id:
            raise ValueError("cannot merge different campaigns")
        for unit in ledger.planned.values():
            merged.add_work(unit)
        for attempts in ledger.results.values():
            for result in attempts:
                merged.add_result(result)
    errors = merged.validate()
    if errors:
        raise ValueError("merged ledger invalid: " + "; ".join(errors))
    return merged


def shard_manifest(
    shards: Sequence[ShardSpec],
    *,
    campaign_id: str,
) -> dict[str, object]:
    if not shards:
        raise ValueError("shards are required")
    payload = {
        "schema": "omega-distributed-shard-manifest/1",
        "campaign_id": campaign_id,
        "shard_count": len(shards),
        "planned_cells": sum(shard.planned_cells for shard in shards),
        "logical_cells": shards[0].logical_cells,
        "shards": [shard.to_dict() for shard in shards],
        "permanent_total_cap": None,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["manifest_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload
