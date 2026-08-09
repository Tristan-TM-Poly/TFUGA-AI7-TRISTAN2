"""Minimal formal multi-scale hypergraph scaffold for Ω-HGFM-MATH-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable


Node = Hashable
Hyperedge = frozenset[Node]


@dataclass(frozen=True)
class HypergraphLevel:
    scale: float
    vertices: frozenset[Node]
    hyperedges: frozenset[Hyperedge]

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError("scale must be positive")
        if any(not edge <= self.vertices for edge in self.hyperedges):
            raise ValueError("every hyperedge must be contained in vertices")


@dataclass(frozen=True)
class ScaleMap:
    """Map vertices at a finer level to vertices at a coarser level."""

    fine_index: int
    coarse_index: int
    mapping: tuple[tuple[Node, Node], ...]

    def as_dict(self) -> dict[Node, Node]:
        return dict(self.mapping)


@dataclass(frozen=True)
class HGFM:
    levels: tuple[HypergraphLevel, ...]
    coarse_maps: tuple[ScaleMap, ...]

    def __post_init__(self) -> None:
        if any(
            self.levels[index].scale >= self.levels[index + 1].scale
            for index in range(len(self.levels) - 1)
        ):
            raise ValueError("levels must be ordered from fine to coarse scale")


def compose_scale_maps(first: ScaleMap, second: ScaleMap) -> dict[Node, Node]:
    """Compose fine->middle and middle->coarse vertex maps."""

    if first.coarse_index != second.fine_index:
        raise ValueError("scale maps are not composable")
    left = first.as_dict()
    right = second.as_dict()
    return {source: right[mid] for source, mid in left.items() if mid in right}


def scale_coherence_defect(
    composed: dict[Node, Node],
    direct: dict[Node, Node],
) -> float:
    """Fraction of jointly-defined sources on which coarse-graining disagrees."""

    domain = set(composed) | set(direct)
    if not domain:
        return 0.0
    mismatches = sum(composed.get(node) != direct.get(node) for node in domain)
    return mismatches / len(domain)


def growth_dimension(vertex_counts: Iterable[int], inverse_scales: Iterable[float]) -> float:
    """Endpoint log-slope diagnostic, not a universal fractal dimension."""

    from math import log

    counts = tuple(vertex_counts)
    scales = tuple(inverse_scales)
    if len(counts) != len(scales) or len(counts) < 2:
        raise ValueError("need equally sized sequences with at least two points")
    if any(count <= 0 for count in counts) or any(scale <= 0 for scale in scales):
        raise ValueError("counts and inverse scales must be positive")
    denominator = log(scales[-1]) - log(scales[0])
    if denominator == 0:
        raise ValueError("endpoint inverse scales must differ")
    return (log(counts[-1]) - log(counts[0])) / denominator
