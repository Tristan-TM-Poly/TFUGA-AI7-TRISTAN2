from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .campaign import (
    CampaignCheckpoint,
    CampaignJob,
    CampaignManifest,
    CampaignShard,
)
from .campaign_runtime import CheckpointArtifact
from .layout import ArenaLayout
from .simulation import AgentGenome, ArenaConfig


CAMPAIGN_BUNDLE_VERSION = "0.1"
WORKER_PROTOCOL_VERSION = "0.1"


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
class WorkerManifest:
    worker_id: str
    protocol_version: str = WORKER_PROTOCOL_VERSION
    max_concurrent_shards: int = 1
    tags: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.worker_id:
            raise ValueError("worker_id cannot be empty")
        if self.protocol_version != WORKER_PROTOCOL_VERSION:
            raise ValueError(f"unsupported worker protocol: {self.protocol_version}")
        if self.max_concurrent_shards < 1:
            raise ValueError("max_concurrent_shards must be >= 1")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("worker tags must be unique")

    @property
    def manifest_receipt(self) -> str:
        self.validate()
        return _canonical_hash(self.normalized_dict())

    def normalized_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "worker_id": self.worker_id,
            "protocol_version": self.protocol_version,
            "max_concurrent_shards": self.max_concurrent_shards,
            "tags": sorted(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkerManifest":
        allowed = {"worker_id", "protocol_version", "max_concurrent_shards", "tags"}
        if set(data) != allowed:
            raise ValueError("invalid worker manifest fields")
        tags_raw = data["tags"]
        if not isinstance(tags_raw, list):
            raise ValueError("worker tags must be a list")
        manifest = cls(
            worker_id=str(data["worker_id"]),
            protocol_version=str(data["protocol_version"]),
            max_concurrent_shards=int(data["max_concurrent_shards"]),
            tags=tuple(sorted(str(tag) for tag in tags_raw)),
        )
        manifest.validate()
        return manifest


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_id: str
    sequence: int
    observed_at: float
    manifest_receipt: str
    heartbeat_receipt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkerRegistry:
    clock: Callable[[], float] = time.monotonic
    manifests: dict[str, WorkerManifest] = field(default_factory=dict)
    heartbeats: dict[str, WorkerHeartbeat] = field(default_factory=dict)

    def register(self, manifest: WorkerManifest) -> None:
        manifest.validate()
        existing = self.manifests.get(manifest.worker_id)
        if existing is not None and existing.manifest_receipt != manifest.manifest_receipt:
            raise ValueError("worker manifest changed without explicit unregister")
        self.manifests[manifest.worker_id] = manifest

    def unregister(self, worker_id: str) -> None:
        self.manifests.pop(worker_id, None)
        self.heartbeats.pop(worker_id, None)

    def heartbeat(self, worker_id: str) -> WorkerHeartbeat:
        manifest = self.manifests.get(worker_id)
        if manifest is None:
            raise ValueError("worker must be registered before heartbeat")
        previous = self.heartbeats.get(worker_id)
        sequence = 1 if previous is None else previous.sequence + 1
        deterministic_payload = {
            "worker_id": worker_id,
            "sequence": sequence,
            "manifest_receipt": manifest.manifest_receipt,
        }
        heartbeat = WorkerHeartbeat(
            worker_id=worker_id,
            sequence=sequence,
            observed_at=float(self.clock()),
            manifest_receipt=manifest.manifest_receipt,
            heartbeat_receipt=_canonical_hash(deterministic_payload),
        )
        self.heartbeats[worker_id] = heartbeat
        return heartbeat

    def is_active(self, worker_id: str, *, ttl_seconds: float, now: float | None = None) -> bool:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        heartbeat = self.heartbeats.get(worker_id)
        if heartbeat is None:
            return False
        instant = float(self.clock() if now is None else now)
        return instant - heartbeat.observed_at <= ttl_seconds

    def active_workers(self, *, ttl_seconds: float, now: float | None = None) -> tuple[str, ...]:
        instant = float(self.clock() if now is None else now)
        return tuple(
            sorted(
                worker_id
                for worker_id in self.manifests
                if self.is_active(worker_id, ttl_seconds=ttl_seconds, now=instant)
            )
        )


@dataclass(frozen=True)
class TTLShardLease:
    shard_id: int
    worker_id: str
    epoch: int
    issued_at: float
    expires_at: float
    lease_token: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TTLLeaseCoordinator:
    plan_receipt: str
    registry: WorkerRegistry
    clock: Callable[[], float] = time.monotonic
    active: dict[int, TTLShardLease] = field(default_factory=dict)
    epochs: dict[int, int] = field(default_factory=dict)
    expired_tokens: list[str] = field(default_factory=list)
    released_tokens: list[str] = field(default_factory=list)

    def expire(self, *, now: float | None = None) -> tuple[TTLShardLease, ...]:
        instant = float(self.clock() if now is None else now)
        expired = tuple(
            lease
            for lease in sorted(self.active.values(), key=lambda item: item.shard_id)
            if lease.expires_at <= instant
        )
        for lease in expired:
            self.active.pop(lease.shard_id, None)
            self.expired_tokens.append(lease.lease_token)
        return expired

    def acquire(
        self,
        shard_id: int,
        worker_id: str,
        *,
        lease_ttl_seconds: float,
        heartbeat_ttl_seconds: float,
    ) -> TTLShardLease:
        if lease_ttl_seconds <= 0 or heartbeat_ttl_seconds <= 0:
            raise ValueError("lease and heartbeat TTLs must be > 0")
        now = float(self.clock())
        self.expire(now=now)
        if not self.registry.is_active(worker_id, ttl_seconds=heartbeat_ttl_seconds, now=now):
            raise ValueError("worker is not heartbeat-active")
        if shard_id in self.active:
            raise ValueError(f"shard {shard_id} already leased")
        epoch = self.epochs.get(shard_id, 0) + 1
        self.epochs[shard_id] = epoch
        deterministic_payload = {
            "plan_receipt": self.plan_receipt,
            "shard_id": int(shard_id),
            "worker_id": worker_id,
            "epoch": epoch,
        }
        lease = TTLShardLease(
            shard_id=int(shard_id),
            worker_id=worker_id,
            epoch=epoch,
            issued_at=now,
            expires_at=now + float(lease_ttl_seconds),
            lease_token=_canonical_hash(deterministic_payload),
        )
        self.active[lease.shard_id] = lease
        return lease

    def renew(
        self,
        lease: TTLShardLease,
        *,
        lease_ttl_seconds: float,
        heartbeat_ttl_seconds: float,
    ) -> TTLShardLease:
        if lease_ttl_seconds <= 0 or heartbeat_ttl_seconds <= 0:
            raise ValueError("lease and heartbeat TTLs must be > 0")
        now = float(self.clock())
        self.expire(now=now)
        active = self.active.get(lease.shard_id)
        if active is None or active.lease_token != lease.lease_token:
            raise ValueError("lease is not active")
        if not self.registry.is_active(lease.worker_id, ttl_seconds=heartbeat_ttl_seconds, now=now):
            raise ValueError("worker is not heartbeat-active")
        renewed = TTLShardLease(
            shard_id=lease.shard_id,
            worker_id=lease.worker_id,
            epoch=lease.epoch,
            issued_at=lease.issued_at,
            expires_at=now + float(lease_ttl_seconds),
            lease_token=lease.lease_token,
        )
        self.active[lease.shard_id] = renewed
        return renewed

    def release(self, lease: TTLShardLease) -> None:
        active = self.active.get(lease.shard_id)
        if active is None or active.lease_token != lease.lease_token:
            raise ValueError("lease is not active")
        del self.active[lease.shard_id]
        self.released_tokens.append(lease.lease_token)


@dataclass(frozen=True)
class ArtifactReceipt:
    content_sha256: str
    byte_count: int
    media_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ArtifactStore(Protocol):
    def put_bytes(self, data: bytes, *, media_type: str) -> ArtifactReceipt: ...
    def get_bytes(self, receipt: ArtifactReceipt) -> bytes: ...


@dataclass
class LocalContentAddressedStore:
    root: Path

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, receipt: ArtifactReceipt) -> Path:
        return self.root / receipt.content_sha256[:2] / receipt.content_sha256

    def put_bytes(self, data: bytes, *, media_type: str = "application/octet-stream") -> ArtifactReceipt:
        if not media_type:
            raise ValueError("media_type cannot be empty")
        digest = hashlib.sha256(data).hexdigest()
        receipt = ArtifactReceipt(digest, len(data), media_type)
        target = self.path_for(receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = target.read_bytes()
            if existing != data:
                raise ValueError("content-address collision or store corruption")
            return receipt
        temp = target.with_name(f".{target.name}.tmp-{os.getpid()}")
        try:
            with temp.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
        return receipt

    def get_bytes(self, receipt: ArtifactReceipt) -> bytes:
        data = self.path_for(receipt).read_bytes()
        if len(data) != receipt.byte_count:
            raise ValueError("artifact byte count mismatch")
        if hashlib.sha256(data).hexdigest() != receipt.content_sha256:
            raise ValueError("artifact content hash mismatch")
        return data


@dataclass(frozen=True)
class CampaignBundle:
    version: str
    manifest: dict[str, Any]
    checkpoint: dict[str, Any] | None
    workers: tuple[dict[str, Any], ...]
    bundle_receipt: str

    @classmethod
    def from_state(
        cls,
        manifest: CampaignManifest,
        *,
        checkpoint: CampaignCheckpoint | None = None,
        workers: tuple[WorkerManifest, ...] = (),
    ) -> "CampaignBundle":
        manifest.validate()
        if checkpoint is not None:
            checkpoint.validate_for(manifest)
        normalized_workers = tuple(
            worker.normalized_dict() for worker in sorted(workers, key=lambda item: item.worker_id)
        )
        if len({worker["worker_id"] for worker in normalized_workers}) != len(normalized_workers):
            raise ValueError("worker IDs in bundle must be unique")
        checkpoint_payload = (
            None if checkpoint is None else CheckpointArtifact.from_checkpoint(checkpoint).to_dict()
        )
        deterministic_payload = {
            "version": CAMPAIGN_BUNDLE_VERSION,
            "manifest": manifest.to_dict(),
            "checkpoint": checkpoint_payload,
            "workers": list(normalized_workers),
        }
        return cls(
            version=CAMPAIGN_BUNDLE_VERSION,
            manifest=manifest.to_dict(),
            checkpoint=checkpoint_payload,
            workers=normalized_workers,
            bundle_receipt=_canonical_hash(deterministic_payload),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CampaignBundle":
        allowed = {"version", "manifest", "checkpoint", "workers", "bundle_receipt"}
        if set(data) != allowed:
            raise ValueError("invalid campaign bundle fields")
        if str(data["version"]) != CAMPAIGN_BUNDLE_VERSION:
            raise ValueError(f"unsupported campaign bundle version: {data['version']}")
        if not isinstance(data["manifest"], dict):
            raise ValueError("bundle manifest must be object")
        checkpoint = data["checkpoint"]
        if checkpoint is not None and not isinstance(checkpoint, dict):
            raise ValueError("bundle checkpoint must be object or null")
        workers_raw = data["workers"]
        if not isinstance(workers_raw, list):
            raise ValueError("bundle workers must be list")
        deterministic_payload = {
            "version": CAMPAIGN_BUNDLE_VERSION,
            "manifest": data["manifest"],
            "checkpoint": checkpoint,
            "workers": workers_raw,
        }
        if _canonical_hash(deterministic_payload) != str(data["bundle_receipt"]):
            raise ValueError("campaign bundle receipt mismatch")
        return cls(
            version=CAMPAIGN_BUNDLE_VERSION,
            manifest=dict(data["manifest"]),
            checkpoint=None if checkpoint is None else dict(checkpoint),
            workers=tuple(dict(worker) for worker in workers_raw),
            bundle_receipt=str(data["bundle_receipt"]),
        )

    @classmethod
    def from_json(cls, text: str) -> "CampaignBundle":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("campaign bundle JSON root must be object")
        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "manifest": self.manifest,
            "checkpoint": self.checkpoint,
            "workers": list(self.workers),
            "bundle_receipt": self.bundle_receipt,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"

    def restore(self) -> tuple[CampaignManifest, CampaignCheckpoint | None, tuple[WorkerManifest, ...]]:
        manifest = _manifest_from_dict(self.manifest)
        workers = tuple(WorkerManifest.from_dict(worker) for worker in self.workers)
        checkpoint = None
        if self.checkpoint is not None:
            checkpoint = CheckpointArtifact.from_dict(self.checkpoint).to_checkpoint(manifest)
        return manifest, checkpoint, workers


def put_bundle(store: ArtifactStore, bundle: CampaignBundle) -> ArtifactReceipt:
    return store.put_bytes(bundle.to_json().encode("utf-8"), media_type="application/vnd.omega-game-campaign-bundle+json")


def get_bundle(store: ArtifactStore, receipt: ArtifactReceipt) -> CampaignBundle:
    return CampaignBundle.from_json(store.get_bytes(receipt).decode("utf-8"))


def _manifest_from_dict(data: Mapping[str, Any]) -> CampaignManifest:
    allowed = {
        "agents", "layouts", "seeds", "mirrored", "arena_template",
        "jobs", "shards", "job_count", "plan_receipt",
    }
    if set(data) != allowed:
        raise ValueError("invalid campaign manifest fields in bundle")
    agents_raw = data["agents"]
    layouts_raw = data["layouts"]
    jobs_raw = data["jobs"]
    shards_raw = data["shards"]
    if not all(isinstance(value, list) for value in (agents_raw, layouts_raw, jobs_raw, shards_raw)):
        raise ValueError("manifest list fields are invalid")
    agents = tuple(AgentGenome(**dict(item)) for item in agents_raw)
    layouts = tuple(ArenaLayout.from_dict(item) for item in layouts_raw)
    arena = ArenaConfig(**dict(data["arena_template"]))
    jobs = tuple(CampaignJob(**dict(item)) for item in jobs_raw)
    shards = tuple(
        CampaignShard(
            shard_id=int(item["shard_id"]),
            job_ids=tuple(str(job_id) for job_id in item["job_ids"]),
        )
        for item in shards_raw
    )
    manifest = CampaignManifest(
        agents=agents,
        layouts=layouts,
        seeds=tuple(int(seed) for seed in data["seeds"]),
        mirrored=bool(data["mirrored"]),
        arena_template=arena,
        jobs=jobs,
        shards=shards,
        plan_receipt=str(data["plan_receipt"]),
    )
    if int(data["job_count"]) != manifest.job_count:
        raise ValueError("manifest job_count mismatch")
    manifest.validate()
    return manifest
