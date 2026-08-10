from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .campaign import (
    CampaignCheckpoint,
    CampaignManifest,
    CampaignResult,
    merge_checkpoints,
    run_campaign_slice,
)


CHECKPOINT_ARTIFACT_VERSION = "0.1"


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class PersistenceReceipt:
    content_sha256: str
    byte_count: int
    checkpoint_receipt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CheckpointArtifact:
    version: str
    plan_receipt: str
    checkpoint_receipt: str
    completed: dict[str, dict[str, Any]]

    @classmethod
    def from_checkpoint(cls, checkpoint: CampaignCheckpoint) -> "CheckpointArtifact":
        payload = checkpoint.to_dict(include_receipt=False)
        return cls(
            version=CHECKPOINT_ARTIFACT_VERSION,
            plan_receipt=checkpoint.plan_receipt,
            checkpoint_receipt=checkpoint.checkpoint_receipt,
            completed=dict(payload["completed"]),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CheckpointArtifact":
        allowed = {"version", "plan_receipt", "checkpoint_receipt", "completed"}
        if set(data) != allowed:
            raise ValueError("invalid checkpoint artifact fields")
        if str(data["version"]) != CHECKPOINT_ARTIFACT_VERSION:
            raise ValueError(f"unsupported checkpoint artifact version: {data['version']}")
        completed = data["completed"]
        if not isinstance(completed, dict):
            raise ValueError("checkpoint artifact completed must be object")
        return cls(
            version=CHECKPOINT_ARTIFACT_VERSION,
            plan_receipt=str(data["plan_receipt"]),
            checkpoint_receipt=str(data["checkpoint_receipt"]),
            completed=dict(completed),
        )

    @classmethod
    def from_json(cls, text: str) -> "CheckpointArtifact":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("checkpoint artifact JSON root must be object")
        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "plan_receipt": self.plan_receipt,
            "checkpoint_receipt": self.checkpoint_receipt,
            "completed": self.completed,
        }

    def to_checkpoint(self, manifest: CampaignManifest) -> CampaignCheckpoint:
        completed: dict[str, CampaignResult] = {}
        for job_id, result_raw in self.completed.items():
            if not isinstance(result_raw, Mapping):
                raise ValueError("checkpoint artifact result must be object")
            result = CampaignResult(**dict(result_raw))
            if result.job_id != job_id:
                raise ValueError("checkpoint artifact key/job_id mismatch")
            completed[job_id] = result
        checkpoint = CampaignCheckpoint(plan_receipt=self.plan_receipt, completed=completed)
        checkpoint.validate_for(manifest)
        if checkpoint.checkpoint_receipt != self.checkpoint_receipt:
            raise ValueError("checkpoint artifact receipt mismatch")
        return checkpoint


def save_checkpoint(path: str | Path, checkpoint: CampaignCheckpoint) -> PersistenceReceipt:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    artifact = CheckpointArtifact.from_checkpoint(checkpoint)
    raw = _canonical_bytes(artifact.to_dict()) + b"\n"
    temp = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        with temp.open("wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()
    return PersistenceReceipt(
        content_sha256=hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
        checkpoint_receipt=checkpoint.checkpoint_receipt,
    )


def load_checkpoint(
    path: str | Path,
    manifest: CampaignManifest,
) -> tuple[CampaignCheckpoint, PersistenceReceipt]:
    raw = Path(path).read_bytes()
    artifact = CheckpointArtifact.from_json(raw.decode("utf-8"))
    checkpoint = artifact.to_checkpoint(manifest)
    receipt = PersistenceReceipt(
        content_sha256=hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
        checkpoint_receipt=checkpoint.checkpoint_receipt,
    )
    return checkpoint, receipt


@dataclass(frozen=True)
class ShardLease:
    shard_id: int
    worker_id: str
    attempt: int
    lease_token: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LeaseLedger:
    plan_receipt: str
    active: dict[int, ShardLease] = field(default_factory=dict)
    released_tokens: list[str] = field(default_factory=list)

    def acquire(self, shard_id: int, worker_id: str, attempt: int) -> ShardLease:
        if shard_id in self.active:
            raise ValueError(f"shard {shard_id} already leased")
        if attempt < 1:
            raise ValueError("lease attempt must be >= 1")
        if not worker_id:
            raise ValueError("worker_id cannot be empty")
        payload = {
            "plan_receipt": self.plan_receipt,
            "shard_id": int(shard_id),
            "worker_id": worker_id,
            "attempt": int(attempt),
        }
        lease = ShardLease(
            shard_id=int(shard_id),
            worker_id=worker_id,
            attempt=int(attempt),
            lease_token=_canonical_hash(payload),
        )
        self.active[lease.shard_id] = lease
        return lease

    def release(self, lease: ShardLease) -> None:
        active = self.active.get(lease.shard_id)
        if active is None or active.lease_token != lease.lease_token:
            raise ValueError("lease is not active")
        del self.active[lease.shard_id]
        self.released_tokens.append(lease.lease_token)


@dataclass(frozen=True)
class ShardFailureReceipt:
    shard_id: int
    attempt: int
    worker_id: str
    error_type: str
    error_message_sha256: str
    failure_receipt: str

    @classmethod
    def from_exception(
        cls,
        *,
        shard_id: int,
        attempt: int,
        worker_id: str,
        error: BaseException,
    ) -> "ShardFailureReceipt":
        error_type = type(error).__name__
        message_hash = hashlib.sha256(str(error).encode("utf-8", errors="replace")).hexdigest()
        payload = {
            "shard_id": int(shard_id),
            "attempt": int(attempt),
            "worker_id": worker_id,
            "error_type": error_type,
            "error_message_sha256": message_hash,
        }
        return cls(
            shard_id=int(shard_id),
            attempt=int(attempt),
            worker_id=worker_id,
            error_type=error_type,
            error_message_sha256=message_hash,
            failure_receipt=_canonical_hash(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessCampaignReport:
    plan_receipt: str
    workers_requested: int
    max_attempts: int
    selected_shards: tuple[int, ...]
    successful_shards: tuple[int, ...]
    failed_shards: tuple[int, ...]
    failures: tuple[ShardFailureReceipt, ...]
    checkpoint_receipt: str
    total_completed_jobs: int
    complete_campaign: bool
    wall_clock_seconds: float

    @property
    def observed_jobs_per_second(self) -> float | None:
        if self.wall_clock_seconds <= 0:
            return None
        return self.total_completed_jobs / self.wall_clock_seconds

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "plan_receipt": self.plan_receipt,
            "workers_requested": self.workers_requested,
            "max_attempts": self.max_attempts,
            "selected_shards": list(self.selected_shards),
            "successful_shards": list(self.successful_shards),
            "failed_shards": list(self.failed_shards),
            "failures": [failure.to_dict() for failure in self.failures],
            "checkpoint_receipt": self.checkpoint_receipt,
            "total_completed_jobs": self.total_completed_jobs,
            "complete_campaign": self.complete_campaign,
            "wall_clock_seconds": self.wall_clock_seconds,
            "observed_jobs_per_second": None
            if self.observed_jobs_per_second is None
            else round(self.observed_jobs_per_second, 6),
        }
        return payload


@dataclass(frozen=True)
class ProcessComparisonReport:
    plan_receipt: str
    workers: int
    sequential_checkpoint_receipt: str
    process_checkpoint_receipt: str
    sequential_wall_clock_seconds: float
    process_wall_clock_seconds: float
    observed_speedup: float | None
    deterministic_equivalence: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_one_shard(manifest: CampaignManifest, shard_id: int) -> CampaignCheckpoint:
    checkpoint, _ = run_campaign_slice(manifest, shard_ids=(shard_id,))
    return checkpoint


def run_process_shards(
    manifest: CampaignManifest,
    *,
    workers: int = 2,
    shard_ids: Iterable[int] | None = None,
    max_attempts: int = 2,
) -> tuple[CampaignCheckpoint, ProcessCampaignReport]:
    manifest.validate()
    if workers < 1:
        raise ValueError("workers must be >= 1")
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    known_shards = {shard.shard_id for shard in manifest.shards}
    selected = tuple(sorted(known_shards)) if shard_ids is None else tuple(sorted(set(int(value) for value in shard_ids)))
    unknown = sorted(set(selected) - known_shards)
    if unknown:
        raise ValueError(f"unknown shard IDs: {','.join(map(str, unknown))}")

    ledger = LeaseLedger(plan_receipt=manifest.plan_receipt)
    successes: dict[int, CampaignCheckpoint] = {}
    failures: list[ShardFailureReceipt] = []
    pending = list(selected)
    start = time.perf_counter()

    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        round_pending = list(pending)
        pending = []
        if workers == 1:
            for shard_id in round_pending:
                worker_id = "controller-0"
                lease = ledger.acquire(shard_id, worker_id, attempt)
                try:
                    successes[shard_id] = _run_one_shard(manifest, shard_id)
                except BaseException as exc:
                    failures.append(
                        ShardFailureReceipt.from_exception(
                            shard_id=shard_id,
                            attempt=attempt,
                            worker_id=worker_id,
                            error=exc,
                        )
                    )
                    pending.append(shard_id)
                finally:
                    ledger.release(lease)
        else:
            max_workers = min(workers, max(1, len(round_pending)))
            with ProcessPoolExecutor(max_workers=max_workers) as pool:
                futures = {}
                leases = {}
                for index, shard_id in enumerate(round_pending):
                    worker_id = f"process-slot-{index % max_workers}"
                    lease = ledger.acquire(shard_id, worker_id, attempt)
                    leases[shard_id] = lease
                    futures[pool.submit(_run_one_shard, manifest, shard_id)] = (shard_id, worker_id)
                for future in as_completed(futures):
                    shard_id, worker_id = futures[future]
                    try:
                        successes[shard_id] = future.result()
                    except BaseException as exc:
                        failures.append(
                            ShardFailureReceipt.from_exception(
                                shard_id=shard_id,
                                attempt=attempt,
                                worker_id=worker_id,
                                error=exc,
                            )
                        )
                        pending.append(shard_id)
                    finally:
                        ledger.release(leases[shard_id])

    elapsed = time.perf_counter() - start
    successful_ids = tuple(sorted(successes))
    failed_ids = tuple(sorted(set(selected) - set(successes)))
    merged = merge_checkpoints(manifest, (successes[shard_id] for shard_id in successful_ids))
    report = ProcessCampaignReport(
        plan_receipt=manifest.plan_receipt,
        workers_requested=workers,
        max_attempts=max_attempts,
        selected_shards=selected,
        successful_shards=successful_ids,
        failed_shards=failed_ids,
        failures=tuple(failures),
        checkpoint_receipt=merged.checkpoint_receipt,
        total_completed_jobs=len(merged.completed),
        complete_campaign=len(merged.completed) == manifest.job_count,
        wall_clock_seconds=round(elapsed, 9),
    )
    return merged, report


def compare_process_execution(
    manifest: CampaignManifest,
    *,
    workers: int = 2,
    max_attempts: int = 2,
) -> ProcessComparisonReport:
    sequential, sequential_report = run_process_shards(
        manifest,
        workers=1,
        max_attempts=max_attempts,
    )
    process, process_report = run_process_shards(
        manifest,
        workers=workers,
        max_attempts=max_attempts,
    )
    equivalent = sequential.checkpoint_receipt == process.checkpoint_receipt
    if not equivalent:
        raise ValueError("process execution differs from sequential deterministic checkpoint")
    speedup = None
    if process_report.wall_clock_seconds > 0:
        speedup = sequential_report.wall_clock_seconds / process_report.wall_clock_seconds
    return ProcessComparisonReport(
        plan_receipt=manifest.plan_receipt,
        workers=workers,
        sequential_checkpoint_receipt=sequential.checkpoint_receipt,
        process_checkpoint_receipt=process.checkpoint_receipt,
        sequential_wall_clock_seconds=sequential_report.wall_clock_seconds,
        process_wall_clock_seconds=process_report.wall_clock_seconds,
        observed_speedup=None if speedup is None else round(speedup, 6),
        deterministic_equivalence=equivalent,
    )
