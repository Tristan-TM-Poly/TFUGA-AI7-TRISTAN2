"""Reusable optimization evidence genes for cross-repository transfer."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class OptimizationGene:
    gene_id: str
    source_repository: str
    source_node: str
    transformation_ids: tuple[str, ...]
    context: Mapping[str, float]
    measured_gain: float
    domain: str
    hardware_id: str
    evidence_level: str
    status: str = "measured-optimization-gene"
    oak_warning: str = (
        "An optimization gene records contextual evidence from a prior result. "
        "Transfer to another workload is a hypothesis requiring fresh validation."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkloadSignature:
    repository: str
    node: str
    context: Mapping[str, float]


@dataclass(frozen=True)
class TransferCandidate:
    gene_id: str
    destination_repository: str
    destination_node: str
    similarity: float
    prior_gain: float
    priority: float
    status: str = "optimization-transfer-candidate"
    oak_warning: str = (
        "Similarity transfers experimental priority, not proof that the source "
        "optimization will preserve semantics or reproduce its gain."
    )


def cosine_context_similarity(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    keys = sorted(set(a) | set(b))
    if not keys:
        return 0.0
    av = [float(a.get(key, 0.0)) for key in keys]
    bv = [float(b.get(key, 0.0)) for key in keys]
    dot = sum(x * y for x, y in zip(av, bv))
    na = math.sqrt(sum(x * x for x in av))
    nb = math.sqrt(sum(y * y for y in bv))
    if na <= 0 or nb <= 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def rank_transfer_candidates(
    genes: Sequence[OptimizationGene],
    workloads: Sequence[WorkloadSignature],
    *,
    minimum_similarity: float = 0.70,
) -> tuple[TransferCandidate, ...]:
    rows: list[TransferCandidate] = []
    for gene in genes:
        for workload in workloads:
            if gene.source_repository == workload.repository and gene.source_node == workload.node:
                continue
            similarity = cosine_context_similarity(gene.context, workload.context)
            if similarity < minimum_similarity:
                continue
            rows.append(
                TransferCandidate(
                    gene_id=gene.gene_id,
                    destination_repository=workload.repository,
                    destination_node=workload.node,
                    similarity=similarity,
                    prior_gain=gene.measured_gain,
                    priority=max(0.0, gene.measured_gain) * similarity,
                )
            )
    return tuple(sorted(rows, key=lambda row: (-row.priority, -row.similarity, row.gene_id, row.destination_node)))
