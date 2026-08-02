"""Deterministic sharding, checkpoints and Merkle-style receipts."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Iterable, Iterator, Mapping, Sequence


def canonical_digest(value: object) -> str:
    return sha256(dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ShardPlan:
    campaign_id: str
    total_items: int
    shard_size: int
    shard_count: int
    plan_digest: str

    @classmethod
    def build(cls, campaign_id: str, total_items: int, shard_size: int) -> "ShardPlan":
        if total_items < 0 or shard_size <= 0:
            raise ValueError("invalid shard dimensions")
        shard_count = (total_items + shard_size - 1) // shard_size
        payload = {"campaign_id": campaign_id, "total_items": total_items, "shard_size": shard_size, "shard_count": shard_count}
        return cls(campaign_id, total_items, shard_size, shard_count, canonical_digest(payload))

    def bounds(self, shard_index: int) -> tuple[int, int]:
        if not 0 <= shard_index < self.shard_count:
            raise IndexError("shard index out of range")
        start = shard_index * self.shard_size
        return start, min(self.total_items, start + self.shard_size)


@dataclass(frozen=True, slots=True)
class ShardReceipt:
    campaign_id: str
    shard_index: int
    start: int
    stop: int
    item_digests: tuple[str, ...]
    shard_digest: str
    previous_receipt_digest: str
    receipt_digest: str

    @classmethod
    def create(
        cls,
        plan: ShardPlan,
        shard_index: int,
        item_digests: Sequence[str],
        *,
        previous_receipt_digest: str = "0" * 64,
    ) -> "ShardReceipt":
        start, stop = plan.bounds(shard_index)
        if len(item_digests) != stop - start:
            raise ValueError("receipt item count does not match shard bounds")
        shard_digest = merkle_root(item_digests)
        payload = {
            "campaign_id": plan.campaign_id,
            "shard_index": shard_index,
            "start": start,
            "stop": stop,
            "item_digests": tuple(item_digests),
            "shard_digest": shard_digest,
            "previous_receipt_digest": previous_receipt_digest,
            "plan_digest": plan.plan_digest,
        }
        return cls(plan.campaign_id, shard_index, start, stop, tuple(item_digests), shard_digest, previous_receipt_digest, canonical_digest(payload))


def merkle_root(leaves: Sequence[str]) -> str:
    if not leaves:
        return sha256(b"").hexdigest()
    layer = [leaf if len(leaf) == 64 else sha256(leaf.encode()).hexdigest() for leaf in leaves]
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [sha256((layer[index] + layer[index + 1]).encode()).hexdigest() for index in range(0, len(layer), 2)]
    return layer[0]


def verify_receipt_chain(plan: ShardPlan, receipts: Sequence[ShardReceipt]) -> bool:
    previous = "0" * 64
    for expected_index, receipt in enumerate(receipts):
        if receipt.campaign_id != plan.campaign_id or receipt.shard_index != expected_index:
            return False
        recreated = ShardReceipt.create(plan, expected_index, receipt.item_digests, previous_receipt_digest=previous)
        if recreated != receipt:
            return False
        previous = receipt.receipt_digest
    return True


def iter_pending_shards(plan: ShardPlan, completed: Iterable[int]) -> Iterator[int]:
    done = set(completed)
    for index in range(plan.shard_count):
        if index not in done:
            yield index


@dataclass(frozen=True, slots=True)
class CampaignCheckpoint:
    campaign_id: str
    completed_shards: tuple[int, ...]
    last_receipt_digest: str
    processed_items: int
    checkpoint_digest: str

    @classmethod
    def from_receipts(cls, plan: ShardPlan, receipts: Sequence[ShardReceipt]) -> "CampaignCheckpoint":
        if not verify_receipt_chain(plan, receipts):
            raise ValueError("invalid receipt chain")
        completed = tuple(receipt.shard_index for receipt in receipts)
        processed = sum(receipt.stop - receipt.start for receipt in receipts)
        last = receipts[-1].receipt_digest if receipts else "0" * 64
        payload = {"campaign_id": plan.campaign_id, "completed_shards": completed, "last_receipt_digest": last, "processed_items": processed, "plan_digest": plan.plan_digest}
        return cls(plan.campaign_id, completed, last, processed, canonical_digest(payload))
