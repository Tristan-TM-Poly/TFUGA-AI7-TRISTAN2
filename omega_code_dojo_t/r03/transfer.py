from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Iterable

from .models import ObservationView, TransferEdge


def infer_transfer_edges(
    observations: Iterable[ObservationView],
    minimum_evidence: int = 2,
) -> tuple[TransferEdge, ...]:
    support: dict[tuple[str, str], int] = defaultdict(int)
    contradiction: dict[tuple[str, str], int] = defaultdict(int)
    campaigns: dict[tuple[str, str], set[str]] = defaultdict(set)

    for observation in observations:
        for left, right in combinations(sorted(set(observation.skills)), 2):
            key = (left, right)
            if observation.success and observation.mutation_score >= 0.8:
                support[key] += 1
            else:
                contradiction[key] += 1
            campaigns[key].add(observation.campaign_id)

    edges = [
        TransferEdge(
            source_skill=left,
            target_skill=right,
            supporting_successes=support[(left, right)],
            contradicting_failures=contradiction[(left, right)],
            distinct_campaigns=len(campaigns[(left, right)]),
        )
        for left, right in sorted(campaigns)
        if support[(left, right)] + contradiction[(left, right)] >= minimum_evidence
    ]
    edges.sort(
        key=lambda item: (
            -item.confidence,
            -(item.supporting_successes + item.contradicting_failures),
            item.source_skill,
            item.target_skill,
        )
    )
    return tuple(edges)
