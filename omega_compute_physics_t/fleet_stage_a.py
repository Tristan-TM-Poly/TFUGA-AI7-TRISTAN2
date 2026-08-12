"""Stage A cross-repository orchestration for Omega Compute Physics R0.5.

Stage A is intentionally static-only: local pinned checkouts are parsed, never
imported or executed. The output seeds workload families and dynamic benchmark
contracts for a later reviewed stage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .fleet import build_fleet_atlas, global_benchmark_priority
from .repo_scanner import RepositoryGenome, scan_repository


@dataclass(frozen=True)
class StageARepositorySummary:
    repository: str
    root: str
    python_files: int
    functions: int
    total_loc: int
    max_loop_depth: int
    recursive_functions: int
    async_functions: int


@dataclass(frozen=True)
class StageABenchmarkSeed:
    repository: str
    module: str
    function: str
    priority_score: float
    structural_scaling_candidate: str


@dataclass(frozen=True)
class FleetStageAReport:
    repositories: tuple[StageARepositorySummary, ...]
    workload_families: int
    workloads: int
    benchmark_seeds: tuple[StageABenchmarkSeed, ...]
    status: str = "fleet-stage-a-static"
    oak_warning: str = (
        "Stage A never executes repository code. Structural priorities and workload families "
        "are measurement-planning heuristics, not runtime or asymptotic claims."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repositories": [asdict(row) for row in self.repositories],
            "workload_families": self.workload_families,
            "workloads": self.workloads,
            "benchmark_seeds": [asdict(row) for row in self.benchmark_seeds],
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


def scan_checkout_fleet(
    checkouts: Mapping[str, str | Path],
    *,
    similarity_threshold: float = 0.92,
    benchmark_limit: int = 100,
) -> tuple[dict[str, RepositoryGenome], FleetStageAReport]:
    if not checkouts:
        raise ValueError("at least one checkout is required")
    genomes: dict[str, RepositoryGenome] = {}
    for repository, root in sorted(checkouts.items()):
        genomes[repository] = scan_repository(root)

    atlas = build_fleet_atlas(genomes, similarity_threshold=similarity_threshold)
    priorities = global_benchmark_priority(genomes, limit=benchmark_limit)
    summaries = tuple(
        StageARepositorySummary(
            repository=repository,
            root=genome.root,
            python_files=genome.python_files,
            functions=genome.functions,
            total_loc=genome.total_loc,
            max_loop_depth=genome.max_loop_depth,
            recursive_functions=genome.recursive_functions,
            async_functions=genome.async_functions,
        )
        for repository, genome in sorted(genomes.items())
    )
    seeds = tuple(
        StageABenchmarkSeed(
            repository=repository,
            module=function.module,
            function=function.qualified_name,
            priority_score=float(score),
            structural_scaling_candidate=function.structural_scaling_candidate,
        )
        for repository, function, score in priorities
    )
    return genomes, FleetStageAReport(
        repositories=summaries,
        workload_families=len(atlas.families),
        workloads=len(atlas.workloads),
        benchmark_seeds=seeds,
    )
