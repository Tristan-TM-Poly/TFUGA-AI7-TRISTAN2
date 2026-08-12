"""Cross-repository fleet atlas for Ω-META-COMPUTE-PHYSICS-T∞.

This module aggregates static RepositoryGenome objects, creates reusable
workload fingerprints and forms transparent similarity families. Families are
measurement-planning aids, not proofs of algorithmic equivalence or universal
complexity classes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence

from .repo_scanner import FunctionGenome, RepositoryGenome

_EPS = 1e-15


@dataclass(frozen=True)
class WorkloadRef:
    repository: str
    module: str
    function: str
    fingerprint: tuple[float, ...]
    structural_scaling_candidate: str


@dataclass(frozen=True)
class WorkloadFamily:
    family_id: str
    centroid: tuple[float, ...]
    members: tuple[WorkloadRef, ...]
    status: str = "static-similarity-family"
    oak_warning: str = (
        "Similarity of static workload fingerprints does not prove identical "
        "runtime scaling, causal mechanism, or algorithmic equivalence."
    )


@dataclass(frozen=True)
class FleetAtlas:
    repositories: tuple[str, ...]
    workloads: tuple[WorkloadRef, ...]
    families: tuple[WorkloadFamily, ...]
    status: str = "cross-repository-static-atlas"

    def to_dict(self) -> dict[str, Any]:
        return {
            "repositories": list(self.repositories),
            "workloads": [asdict(row) for row in self.workloads],
            "families": [
                {
                    **asdict(family),
                    "members": [asdict(member) for member in family.members],
                }
                for family in self.families
            ],
            "status": self.status,
            "oak_warning": (
                "The fleet atlas is a static map for benchmark planning. Dynamic "
                "resource laws require measured ResourceSamples and OAK validation."
            ),
        }


def _fingerprint(function: FunctionGenome) -> tuple[float, ...]:
    # log1p compresses very large LOC/call-count differences while preserving
    # zeros and keeping the signature dependency-free and deterministic.
    raw = function.vector()
    scaled = tuple(math.log1p(max(value, 0.0)) for value in raw)
    norm = math.sqrt(sum(value * value for value in scaled))
    if norm <= _EPS:
        return scaled
    return tuple(value / norm for value in scaled)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("fingerprint dimensions must match")
    nl = math.sqrt(sum(value * value for value in left))
    nr = math.sqrt(sum(value * value for value in right))
    if nl <= _EPS or nr <= _EPS:
        return 1.0 if nl <= _EPS and nr <= _EPS else 0.0
    return sum(a * b for a, b in zip(left, right)) / (nl * nr)


def workload_refs(genomes: Mapping[str, RepositoryGenome]) -> tuple[WorkloadRef, ...]:
    rows: list[WorkloadRef] = []
    for repository, genome in sorted(genomes.items()):
        for module in genome.modules:
            for function in module.functions:
                rows.append(
                    WorkloadRef(
                        repository=repository,
                        module=function.module,
                        function=function.qualified_name,
                        fingerprint=_fingerprint(function),
                        structural_scaling_candidate=function.structural_scaling_candidate,
                    )
                )
    return tuple(rows)


def _centroid(members: Sequence[WorkloadRef]) -> tuple[float, ...]:
    if not members:
        raise ValueError("cannot compute an empty family centroid")
    dimensions = len(members[0].fingerprint)
    values = [
        sum(member.fingerprint[index] for member in members) / len(members)
        for index in range(dimensions)
    ]
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= _EPS:
        return tuple(values)
    return tuple(value / norm for value in values)


def build_workload_families(
    workloads: Sequence[WorkloadRef],
    *,
    similarity_threshold: float = 0.92,
) -> tuple[WorkloadFamily, ...]:
    """Greedy deterministic clustering of static workload fingerprints."""

    if not -1.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold must be in [-1, 1]")
    groups: list[list[WorkloadRef]] = []
    for workload in sorted(workloads, key=lambda row: (row.repository, row.module, row.function)):
        best_index = None
        best_similarity = -math.inf
        for index, members in enumerate(groups):
            similarity = cosine_similarity(workload.fingerprint, _centroid(members))
            if similarity >= similarity_threshold and similarity > best_similarity:
                best_index = index
                best_similarity = similarity
        if best_index is None:
            groups.append([workload])
        else:
            groups[best_index].append(workload)
    families: list[WorkloadFamily] = []
    for index, members in enumerate(groups, start=1):
        families.append(
            WorkloadFamily(
                family_id=f"WF-{index:04d}",
                centroid=_centroid(members),
                members=tuple(members),
            )
        )
    return tuple(families)


def build_fleet_atlas(
    genomes: Mapping[str, RepositoryGenome],
    *,
    similarity_threshold: float = 0.92,
) -> FleetAtlas:
    rows = workload_refs(genomes)
    return FleetAtlas(
        repositories=tuple(sorted(genomes)),
        workloads=rows,
        families=build_workload_families(rows, similarity_threshold=similarity_threshold),
    )


def global_benchmark_priority(
    genomes: Mapping[str, RepositoryGenome],
    *,
    limit: int = 100,
) -> tuple[tuple[str, FunctionGenome, float], ...]:
    """Rank functions across repositories by transparent measurement priority."""

    rows: list[tuple[str, FunctionGenome, float]] = []
    for repository, genome in genomes.items():
        for module in genome.modules:
            for function in module.functions:
                score = (
                    8.0 * function.max_loop_depth
                    + 2.0 * function.loops
                    + 1.5 * function.branches
                    + 0.5 * function.calls
                    + 0.15 * function.loc
                    + 8.0 * function.direct_recursion
                    + 2.0 * function.async_function
                )
                rows.append((repository, function, score))
    rows.sort(key=lambda row: (-row[2], row[0], row[1].module, row[1].qualified_name))
    return tuple(rows[:limit])
