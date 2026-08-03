"""Deterministic Byzantine-worker simulation and quorum evidence.

This is a software adversarial benchmark, not a proof of Byzantine fault
tolerance for real networks, identities, clocks, or infrastructures.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable, Mapping


@dataclass(frozen=True)
class WorkerVote:
    worker_id: str
    item_id: str
    payload_digest: str
    result_digest: str
    epoch: int
    identity_group: str
    revoked: bool = False


@dataclass(frozen=True)
class QuorumDecision:
    item_id: str
    accepted_result_digest: str | None
    valid_votes: int
    unique_identity_groups: int
    threshold: int
    equivocations: tuple[str, ...]
    rejected_reasons: tuple[str, ...]
    claim: str = "deterministic_quorum_simulation_only"


def decide_quorum(
    votes: Iterable[WorkerVote],
    *,
    expected_payload_digest: str,
    epoch: int,
    threshold: int,
    minimum_identity_groups: int = 1,
) -> QuorumDecision:
    items = tuple(votes)
    if threshold <= 0 or minimum_identity_groups <= 0:
        raise ValueError("thresholds must be positive")
    if not items:
        raise ValueError("votes cannot be empty")
    item_ids = {vote.item_id for vote in items}
    if len(item_ids) != 1:
        raise ValueError("all votes must target one item")
    by_worker: dict[str, set[str]] = defaultdict(set)
    rejected: list[str] = []
    valid: list[WorkerVote] = []
    for vote in items:
        by_worker[vote.worker_id].add(vote.result_digest)
        if vote.revoked:
            rejected.append(f"revoked:{vote.worker_id}")
        elif vote.epoch != epoch:
            rejected.append(f"wrong_epoch:{vote.worker_id}")
        elif vote.payload_digest != expected_payload_digest:
            rejected.append(f"payload_mismatch:{vote.worker_id}")
        elif not vote.worker_id.strip() or not vote.identity_group.strip():
            rejected.append("blank_identity")
        else:
            valid.append(vote)
    equivocations = tuple(sorted(worker for worker, digests in by_worker.items() if len(digests) > 1))
    valid = [vote for vote in valid if vote.worker_id not in equivocations]
    groups_by_result: dict[str, set[str]] = defaultdict(set)
    workers_by_result: dict[str, set[str]] = defaultdict(set)
    for vote in valid:
        groups_by_result[vote.result_digest].add(vote.identity_group)
        workers_by_result[vote.result_digest].add(vote.worker_id)
    eligible = [
        digest
        for digest in groups_by_result
        if len(workers_by_result[digest]) >= threshold and len(groups_by_result[digest]) >= minimum_identity_groups
    ]
    accepted = sorted(eligible)[0] if len(eligible) == 1 else None
    if len(eligible) > 1:
        rejected.append("conflicting_quorums")
    valid_votes = len(workers_by_result.get(accepted, set())) if accepted else 0
    unique_groups = len(groups_by_result.get(accepted, set())) if accepted else 0
    return QuorumDecision(
        item_id=next(iter(item_ids)),
        accepted_result_digest=accepted,
        valid_votes=valid_votes,
        unique_identity_groups=unique_groups,
        threshold=threshold,
        equivocations=equivocations,
        rejected_reasons=tuple(sorted(set(rejected))),
    )


def deterministic_fault_campaign(
    *,
    honest_workers: int,
    byzantine_workers: int,
    threshold: int,
) -> Mapping[str, QuorumDecision]:
    if honest_workers < 0 or byzantine_workers < 0:
        raise ValueError("worker counts cannot be negative")
    payload = "sha256:payload"
    votes: list[WorkerVote] = []
    for index in range(honest_workers):
        votes.append(WorkerVote(f"honest-{index}", "item", payload, "sha256:good", 1, f"g{index % 3}"))
    for index in range(byzantine_workers):
        votes.append(WorkerVote(f"bad-{index}", "item", payload, f"sha256:bad-{index % 2}", 1, f"b{index}"))
    baseline = decide_quorum(votes, expected_payload_digest=payload, epoch=1, threshold=threshold, minimum_identity_groups=2)
    equivocation_votes = votes + [WorkerVote("bad-0", "item", payload, "sha256:other", 1, "b0")]
    equivocation = decide_quorum(equivocation_votes, expected_payload_digest=payload, epoch=1, threshold=threshold, minimum_identity_groups=2)
    return {"baseline": baseline, "equivocation": equivocation}
