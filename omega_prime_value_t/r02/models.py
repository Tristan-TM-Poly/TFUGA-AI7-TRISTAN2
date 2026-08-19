from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    PLANNED = "planned"
    FILTERED_COMPOSITE = "filtered_composite"
    COMPOSITE = "composite"
    PROBABLE_PRIME = "probable_prime"
    PROVEN_PRIME = "proven_prime"
    CERTIFIED = "certified"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CandidateTask:
    task_id: str
    shard_id: str
    ordinal: int
    family: str
    exponent: int
    k: int
    value: int
    state: TaskState = TaskState.PLANNED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["value"] = str(self.value)
        return payload


@dataclass(frozen=True, slots=True)
class CampaignManifest:
    manifest_version: str
    campaign_id: str
    policy: dict[str, Any]
    shard_count: int
    task_count: int
    tasks: tuple[CandidateTask, ...]
    sha256: str
    claims: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "campaign_id": self.campaign_id,
            "policy": self.policy,
            "shard_count": self.shard_count,
            "task_count": self.task_count,
            "tasks": [task.to_dict() for task in self.tasks],
            "sha256": self.sha256,
            "claims": self.claims,
        }


@dataclass(frozen=True, slots=True)
class TaskReceipt:
    task_id: str
    state: TaskState
    candidate: str
    factor: int | None = None
    certificate_id: str | None = None
    certificate_sha256: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


@dataclass(slots=True)
class CampaignSummary:
    campaign_id: str
    planned: int
    processed: int = 0
    filtered_composites: int = 0
    composites: int = 0
    probable_primes: int = 0
    proven_primes: int = 0
    certified: int = 0
    failed: int = 0
    receipts: list[TaskReceipt] = field(default_factory=list)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    claims: dict[str, bool] = field(
        default_factory=lambda: {
            "external_novelty_checked": False,
            "record_claimed": False,
            "economic_value_guaranteed": False,
            "cryptographic_secret_material": False,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "planned": self.planned,
            "processed": self.processed,
            "filtered_composites": self.filtered_composites,
            "composites": self.composites,
            "probable_primes": self.probable_primes,
            "proven_primes": self.proven_primes,
            "certified": self.certified,
            "failed": self.failed,
            "receipts": [receipt.to_dict() for receipt in self.receipts],
            "checkpoint": self.checkpoint,
            "claims": self.claims,
        }
