from __future__ import annotations

import time
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .engine import artifact_from_mapping, evaluate_artifact
from .store import CampaignStore
from .transparency import digest_payload, merkle_root


@dataclass(frozen=True)
class CampaignConfig:
    campaign_id: str
    checkpoint_every: int = 1000
    initial_batch_size: int = 256
    target_batch_seconds: float = 0.25
    minimum_score: float = 0.0
    stop_after: int | None = None

    def validate(self) -> None:
        if not self.campaign_id.strip():
            raise ValueError("campaign_id is required")
        if self.checkpoint_every <= 0 or self.initial_batch_size <= 0:
            raise ValueError("batch and checkpoint sizes must be positive")
        if self.target_batch_seconds <= 0:
            raise ValueError("target_batch_seconds must be positive")
        if not 0 <= self.minimum_score <= 1:
            raise ValueError("minimum_score must be between 0 and 1")
        if self.stop_after is not None and self.stop_after <= 0:
            raise ValueError("stop_after must be positive when supplied")


@dataclass(frozen=True)
class CampaignReceipt:
    campaign_id: str
    seen: int
    accepted: int
    inserted: int
    updated: int
    duplicates: int
    quarantined: int
    final_batch_size: int
    source_exhausted: bool
    artifact_merkle_root: str
    receipt_hash: str
    checkpoint_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_shard(value: str, shard_count: int) -> int:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    return int(digest_payload(value)[:16], 16) % shard_count


def _adapt_batch(current: int, elapsed: float, target: float) -> int:
    if elapsed <= 0:
        return current * 2
    ratio = target / elapsed
    factor = max(0.5, min(2.0, ratio))
    return max(1, int(current * factor))


def run_campaign(
    records: Iterable[Mapping[str, Any]],
    store: CampaignStore,
    config: CampaignConfig,
    *,
    review_approved: bool = False,
) -> CampaignReceipt:
    config.validate()
    checkpoint = store.load_checkpoint(config.campaign_id)
    resume_offset = checkpoint["source_offset"] if checkpoint else 0
    accepted = checkpoint["accepted"] if checkpoint else 0
    duplicates = checkpoint["duplicates"] if checkpoint else 0
    quarantined = checkpoint["quarantined"] if checkpoint else 0
    inserted = updated = 0
    seen = resume_offset
    batch_size = config.initial_batch_size
    source_exhausted = True
    iterator = iter(records)

    for _ in range(resume_offset):
        try:
            next(iterator)
        except StopIteration:
            break

    last_checkpoint_bucket = seen // config.checkpoint_every
    while True:
        requested_batch_size = batch_size
        if config.stop_after is not None:
            remaining = config.stop_after - seen
            if remaining <= 0:
                source_exhausted = False
                break
            requested_batch_size = min(requested_batch_size, remaining)
        batch: list[Mapping[str, Any]] = []
        for _ in range(requested_batch_size):
            try:
                batch.append(next(iterator))
            except StopIteration:
                break
        if not batch:
            break

        started = time.perf_counter()
        valid_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
        quarantine_payloads: list[dict[str, Any]] = []
        for local_index, record in enumerate(batch):
            source_offset = seen + local_index
            try:
                artifact = artifact_from_mapping(record)
                assessment = evaluate_artifact(
                    artifact,
                    review_approved=review_approved,
                )
                if assessment["score"] < config.minimum_score:
                    quarantined += 1
                    continue
                valid_pairs.append((artifact.to_dict(), assessment))
            except (KeyError, TypeError, ValueError) as error:
                quarantined += 1
                quarantine_payloads.append(
                    {
                        "source_offset": source_offset,
                        "error_type": type(error).__name__,
                        "message": str(error)[:300],
                    }
                )
        counts = store.upsert_artifacts_batch(valid_pairs)
        accepted += len(valid_pairs)
        inserted += counts["inserted"]
        updated += counts["updated"]
        duplicates += counts["duplicates"]
        for payload in quarantine_payloads:
            store.append_event(config.campaign_id, "quarantine", payload)
        seen += len(batch)

        current_bucket = seen // config.checkpoint_every
        if current_bucket > last_checkpoint_bucket:
            store.save_checkpoint(
                config.campaign_id,
                source_offset=seen,
                accepted=accepted,
                duplicates=duplicates,
                quarantined=quarantined,
                state={"batch_size": batch_size},
            )
            last_checkpoint_bucket = current_bucket

        elapsed = time.perf_counter() - started
        batch_size = _adapt_batch(batch_size, elapsed, config.target_batch_seconds)
        if len(batch) < requested_batch_size:
            source_exhausted = True
            break
        if config.stop_after is not None and seen >= config.stop_after:
            source_exhausted = False
            break

    root = merkle_root(store.iter_artifact_hashes())
    checkpoint_hash = store.save_checkpoint(
        config.campaign_id,
        source_offset=seen,
        accepted=accepted,
        duplicates=duplicates,
        quarantined=quarantined,
        state={
            "batch_size": batch_size,
            "artifact_merkle_root": root,
            "source_exhausted": source_exhausted,
        },
    )
    body = {
        "campaign_id": config.campaign_id,
        "seen": seen,
        "accepted": accepted,
        "inserted": inserted,
        "updated": updated,
        "duplicates": duplicates,
        "quarantined": quarantined,
        "final_batch_size": batch_size,
        "source_exhausted": source_exhausted,
        "artifact_merkle_root": root,
        "checkpoint_hash": checkpoint_hash,
    }
    receipt = CampaignReceipt(**body, receipt_hash=digest_payload(body))
    store.append_event(config.campaign_id, "campaign_receipt", receipt.to_dict())
    return receipt


def synthetic_artifacts(
    count: int,
    *,
    namespace: str = "SYNTH",
) -> Iterator[dict[str, Any]]:
    """Generate finite deterministic fixtures lazily; synthetic records are never traction."""
    if count < 0:
        raise ValueError("count must be non-negative")
    for index in range(count):
        demonstrated = index % 5 == 0
        yield {
            "artifact_id": f"{namespace}-{index:012d}",
            "title": f"Synthetic capability fixture {index}",
            "problem": "Exercise streaming, deduplication, checkpoints, and evidence routing.",
            "actor": "OAKBench",
            "oak_status": "D" if demonstrated else "E",
            "disclosure": "OPEN_PUBLIC",
            "revenue_paths": ["fixed_scope_service"],
            "evidence": {
                "tests": index % 31,
                "reproducible_demo": demonstrated,
                "benchmark": index % 7 == 0,
                "external_reproduction": False,
                "paying_user": False,
                "limitations_documented": True,
            },
            "utility": ((index % 90) + 10) / 100,
            "reuse": ((index * 3 % 90) + 10) / 100,
            "discoverability": ((index * 5 % 80) + 10) / 100,
            "trust": ((index * 7 % 80) + 15) / 100,
            "conversion_clarity": ((index * 11 % 80) + 10) / 100,
            "noise": (index % 30) / 100,
            "maintenance_burden": (index % 50) / 100,
            "ip_legal_risk": (index % 20) / 100,
            "safety_privacy_risk": (index % 15) / 100,
            "risks": ["synthetic fixture; not market evidence"],
            "next_action": "retain only for capacity validation",
        }
