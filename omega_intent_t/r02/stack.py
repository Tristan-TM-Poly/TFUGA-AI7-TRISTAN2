from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable, Mapping

from .models import RISK_LEVELS, StackShard, WorkRecord, stable_digest


_APPROVAL_RISKS = frozenset({"ip_sensitive", "public", "irreversible"})


class StackPlanner:
    """Compile a work DAG into deterministic, reversible stacked-PR shards."""

    def __init__(
        self,
        *,
        max_items_per_shard: int = 128,
        max_bytes_per_shard: int = 2 * 1024 * 1024,
        branch_prefix: str = "feat/omega-intent-r02",
    ) -> None:
        if max_items_per_shard < 1 or max_bytes_per_shard < 1:
            raise ValueError("shard budgets must be positive")
        self.max_items_per_shard = max_items_per_shard
        self.max_bytes_per_shard = max_bytes_per_shard
        self.branch_prefix = branch_prefix.rstrip("/")

    def topological_levels(self, records: Iterable[WorkRecord]) -> dict[str, int]:
        ordered = tuple(records)
        by_id = {record.record_id: record for record in ordered}
        if len(by_id) != len(ordered):
            raise ValueError("duplicate work unit identifiers")
        missing = {
            dependency
            for record in ordered
            for dependency in record.dependency_ids
            if dependency not in by_id
        }
        if missing:
            raise ValueError(f"missing dependencies: {sorted(missing)}")

        indegree = {record_id: 0 for record_id in by_id}
        children: dict[str, list[str]] = defaultdict(list)
        for record in ordered:
            for dependency in record.dependency_ids:
                indegree[record.record_id] += 1
                children[dependency].append(record.record_id)

        queue = deque(sorted(record_id for record_id, degree in indegree.items() if degree == 0))
        levels = {record_id: 0 for record_id in queue}
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in sorted(children[current]):
                levels[child] = max(levels.get(child, 0), levels[current] + 1)
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(by_id):
            cycle_nodes = sorted(record_id for record_id, degree in indegree.items() if degree > 0)
            raise ValueError(f"cycle detected: {cycle_nodes}")
        return levels

    def plan(self, records: Iterable[WorkRecord]) -> tuple[StackShard, ...]:
        ordered = tuple(records)
        levels = self.topological_levels(ordered)
        by_level: dict[int, list[WorkRecord]] = defaultdict(list)
        for record in ordered:
            by_level[levels[record.record_id]].append(record)

        shards: list[StackShard] = []
        record_to_shard: dict[str, str] = {}
        for level in sorted(by_level):
            buckets: dict[str, list[WorkRecord]] = defaultdict(list)
            for record in sorted(by_level[level], key=lambda item: (item.risk, item.kind, item.record_id)):
                risk_bucket = record.risk if record.risk in _APPROVAL_RISKS else "standard"
                buckets[risk_bucket].append(record)

            for risk_bucket in sorted(buckets):
                sequence = 0
                current: list[WorkRecord] = []
                current_bytes = 0
                for record in buckets[risk_bucket]:
                    would_exceed = (
                        current
                        and (
                            len(current) + 1 > self.max_items_per_shard
                            or current_bytes + record.estimated_bytes > self.max_bytes_per_shard
                        )
                    )
                    if would_exceed:
                        sequence += 1
                        shard = self._make_shard(level, sequence, risk_bucket, current, record_to_shard)
                        shards.append(shard)
                        for item in current:
                            record_to_shard[item.record_id] = shard.shard_id
                        current = []
                        current_bytes = 0
                    current.append(record)
                    current_bytes += record.estimated_bytes
                if current:
                    sequence += 1
                    shard = self._make_shard(level, sequence, risk_bucket, current, record_to_shard)
                    shards.append(shard)
                    for item in current:
                        record_to_shard[item.record_id] = shard.shard_id

        return tuple(shards)

    def _make_shard(
        self,
        level: int,
        sequence: int,
        risk_bucket: str,
        records: list[WorkRecord],
        record_to_shard: Mapping[str, str],
    ) -> StackShard:
        dependencies = sorted(
            {
                record_to_shard[dependency]
                for record in records
                for dependency in record.dependency_ids
                if dependency in record_to_shard
            }
        )
        risks = tuple(sorted({record.risk for record in records}, key=RISK_LEVELS.index))
        identity = {
            "level": level,
            "sequence": sequence,
            "risk_bucket": risk_bucket,
            "work_unit_ids": [record.record_id for record in records],
            "depends_on_shards": dependencies,
        }
        shard_id = f"STACK-{stable_digest(identity)[:20].upper()}"
        branch = f"{self.branch_prefix}/l{level:04d}-{risk_bucket}-{sequence:04d}-{shard_id[-8:].lower()}"
        return StackShard(
            shard_id=shard_id,
            branch=branch,
            level=level,
            sequence=sequence,
            work_unit_ids=tuple(record.record_id for record in records),
            estimated_bytes=sum(record.estimated_bytes for record in records),
            risks=risks,
            depends_on_shards=tuple(dependencies),
            requires_human_approval=any(risk in _APPROVAL_RISKS for risk in risks),
        )

    @staticmethod
    def rollback_plan(shards: Iterable[StackShard]) -> list[dict[str, object]]:
        ordered = tuple(shards)
        return [
            {
                "order": index,
                "shard_id": shard.shard_id,
                "branch": shard.branch,
                "action": "revert_or_close_without_merge",
            }
            for index, shard in enumerate(reversed(ordered), start=1)
        ]

    def manifest(self, records: Iterable[WorkRecord]) -> dict[str, object]:
        shards = self.plan(records)
        return {
            "schema": "omega-intent-stack-plan/v2",
            "shards": [shard.to_dict() for shard in shards],
            "rollback": self.rollback_plan(shards),
            "max_items_per_shard": self.max_items_per_shard,
            "max_bytes_per_shard": self.max_bytes_per_shard,
            "remote_mutations": 0,
            "automatic_merge": False,
        }
