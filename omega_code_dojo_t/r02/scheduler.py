from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable

from .hashing import stable_id


@dataclass(frozen=True)
class ShardPlan:
    shard_id: str
    start_ordinal: int
    stop_ordinal: int
    budget: int
    runner_class: str

    @property
    def size(self) -> int:
        return self.stop_ordinal - self.start_ordinal

    def to_dict(self) -> dict[str, object]:
        return {
            "shard_id": self.shard_id,
            "start_ordinal": self.start_ordinal,
            "stop_ordinal": self.stop_ordinal,
            "size": self.size,
            "budget": self.budget,
            "runner_class": self.runner_class,
        }


class HierarchicalScheduler:
    """Builds finite resumable shards without asserting a global permanent cap."""

    def plan(
        self,
        *,
        campaign_id: str,
        start_ordinal: int,
        materialization_budget: int,
        shard_size: int,
        runner_classes: Iterable[str] = ("standard",),
    ) -> tuple[ShardPlan, ...]:
        if start_ordinal < 0:
            raise ValueError("start_ordinal must be non-negative")
        if materialization_budget <= 0:
            raise ValueError("materialization_budget must be positive")
        if shard_size <= 0:
            raise ValueError("shard_size must be positive")
        runners = tuple(runner_classes)
        if not runners:
            raise ValueError("at least one runner class is required")

        shard_count = ceil(materialization_budget / shard_size)
        shards: list[ShardPlan] = []
        allocated = 0
        cursor = start_ordinal
        for index in range(shard_count):
            budget = min(shard_size, materialization_budget - allocated)
            stop = cursor + budget
            runner = runners[index % len(runners)]
            shard_id = stable_id(
                "shard",
                [campaign_id, index, cursor, stop, runner],
                length=16,
            )
            shards.append(
                ShardPlan(
                    shard_id=shard_id,
                    start_ordinal=cursor,
                    stop_ordinal=stop,
                    budget=budget,
                    runner_class=runner,
                )
            )
            allocated += budget
            cursor = stop
        return tuple(shards)

    @staticmethod
    def resume_ordinal(shards: Iterable[ShardPlan]) -> int:
        material = tuple(shards)
        return max((shard.stop_ordinal for shard in material), default=0)
