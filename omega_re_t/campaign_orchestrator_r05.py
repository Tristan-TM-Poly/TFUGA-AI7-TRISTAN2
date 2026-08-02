"""Finite-run orchestrator over an indexable frontier with no permanent cap."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Callable, Iterable, Mapping


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ResourceEnvelope:
    max_items: int
    max_cost_units: float
    max_failures: int

    def __post_init__(self) -> None:
        if self.max_items <= 0 or self.max_cost_units <= 0.0 or self.max_failures < 0:
            raise ValueError("invalid resource envelope")


@dataclass(frozen=True)
class CampaignItemResult:
    index: int
    item_digest: str
    result_digest: str | None
    cost_units: float
    passed: bool
    error: str | None


@dataclass(frozen=True)
class CampaignCheckpoint:
    start_index: int
    next_index: int
    evaluated_count: int
    passed_count: int
    failed_count: int
    consumed_cost_units: float
    chain_digest: str
    recommended_next_batch: int
    permanent_total_cap: None = None
    claim: str = "finite_software_campaign_only"


def plan_shards(*, start_index: int, count: int, shard_count: int) -> tuple[tuple[int, int], ...]:
    if start_index < 0 or count < 0 or shard_count <= 0:
        raise ValueError("invalid shard plan")
    if count == 0:
        return ()
    active = min(count, shard_count)
    base, remainder = divmod(count, active)
    shards = []
    cursor = start_index
    for shard in range(active):
        size = base + (1 if shard < remainder else 0)
        shards.append((cursor, size))
        cursor += size
    return tuple(shards)


def run_campaign(
    *,
    start_index: int,
    envelope: ResourceEnvelope,
    generator: Callable[[int], Mapping[str, Any]],
    evaluator: Callable[[Mapping[str, Any]], tuple[bool, Mapping[str, Any], float]],
    previous_chain_digest: str = "sha256:" + "0" * 64,
) -> tuple[tuple[CampaignItemResult, ...], CampaignCheckpoint]:
    results: list[CampaignItemResult] = []
    consumed = 0.0
    failures = 0
    chain = previous_chain_digest
    for offset in range(envelope.max_items):
        index = start_index + offset
        item = generator(index)
        item_digest = _digest(item)
        try:
            passed, payload, cost = evaluator(item)
            cost = float(cost)
            if not math.isfinite(cost) or cost < 0.0:
                raise ValueError("invalid evaluator cost")
            if consumed + cost > envelope.max_cost_units:
                break
            result_digest = _digest(payload)
            error = None
        except Exception as exc:
            passed = False
            cost = 0.0
            result_digest = None
            error = f"{type(exc).__name__}:{exc}"
        if not passed:
            failures += 1
        evidence = {
            "index": index,
            "item_digest": item_digest,
            "result_digest": result_digest,
            "cost": cost,
            "passed": passed,
            "error": error,
            "previous": chain,
        }
        chain = _digest(evidence)
        consumed += cost
        results.append(CampaignItemResult(index, item_digest, result_digest, cost, passed, error))
        if failures > envelope.max_failures:
            break
    evaluated = len(results)
    passed_count = sum(item.passed for item in results)
    failure_rate = 0.0 if evaluated == 0 else (evaluated - passed_count) / evaluated
    cost_fraction = consumed / envelope.max_cost_units
    pressure = max(failure_rate, cost_fraction)
    recommended = max(1, int(envelope.max_items * max(0.1, 1.0 - pressure)))
    checkpoint = CampaignCheckpoint(
        start_index=start_index,
        next_index=start_index + evaluated,
        evaluated_count=evaluated,
        passed_count=passed_count,
        failed_count=evaluated - passed_count,
        consumed_cost_units=consumed,
        chain_digest=chain,
        recommended_next_batch=recommended,
    )
    return tuple(results), checkpoint


def merge_shard_results(
    shards: Iterable[tuple[tuple[CampaignItemResult, ...], CampaignCheckpoint]],
) -> tuple[CampaignItemResult, ...]:
    materialized = tuple(shards)
    results = sorted((item for shard, _ in materialized for item in shard), key=lambda item: item.index)
    indices = [item.index for item in results]
    if len(indices) != len(set(indices)):
        raise ValueError("overlapping shard results")
    if indices and indices != list(range(indices[0], indices[-1] + 1)):
        raise ValueError("gap in shard results")
    return tuple(results)
