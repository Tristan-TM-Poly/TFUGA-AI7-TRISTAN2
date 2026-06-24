"""Compact spectral descriptors for Omega-PSPT++.

Dependency-free graph descriptors for small solid-phase prototypes.
These are OAK-2 descriptors, not experimental claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence, Tuple

Node = Tuple[int, ...]
Edge = Tuple[Node, Node]


@dataclass(frozen=True)
class SpectralSummary:
    nodes: int
    edges: int
    trace_a2: float
    trace_a3: float
    trace_a4: float
    triangles: int
    average_degree: float
    degree_variance: float


def canonical_edge(a: Node, b: Node) -> Edge:
    return (a, b) if a <= b else (b, a)


def adjacency_sets(edges: Iterable[Edge]) -> Dict[Node, set[Node]]:
    adjacency: Dict[Node, set[Node]] = {}
    for a, b in edges:
        if a == b:
            continue
        a, b = canonical_edge(a, b)
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    return adjacency


def count_triangles(adjacency: Mapping[Node, set[Node]]) -> int:
    nodes = sorted(adjacency)
    order = {node: i for i, node in enumerate(nodes)}
    total = 0
    for u in nodes:
        for v in adjacency[u]:
            if order[v] <= order[u]:
                continue
            total += sum(1 for w in adjacency[u] & adjacency[v] if order[w] > order[v])
    return total


def trace_a4(adjacency: Mapping[Node, set[Node]]) -> int:
    total = 0
    for node, neighbors in adjacency.items():
        two_step: Dict[Node, int] = {}
        for mid in neighbors:
            for end in adjacency[mid]:
                two_step[end] = two_step.get(end, 0) + 1
        total += sum(count * count for count in two_step.values())
    return total


def spectral_summary(edges: Iterable[Edge]) -> SpectralSummary:
    edge_list = [canonical_edge(*edge) for edge in edges]
    adjacency = adjacency_sets(edge_list)
    n = len(adjacency)
    e = sum(len(neighbors) for neighbors in adjacency.values()) // 2
    triangles = count_triangles(adjacency)
    degrees = [len(neighbors) for neighbors in adjacency.values()]
    avg_degree = sum(degrees) / n if n else 0.0
    degree_variance = sum((d - avg_degree) ** 2 for d in degrees) / n if n else 0.0
    return SpectralSummary(
        nodes=n,
        edges=e,
        trace_a2=float(2 * e),
        trace_a3=float(6 * triangles),
        trace_a4=float(trace_a4(adjacency)),
        triangles=triangles,
        average_degree=avg_degree,
        degree_variance=degree_variance,
    )


def tight_binding_matrix(nodes: Sequence[Node], edges: Iterable[Edge], hopping: float = -1.0) -> list[list[float]]:
    index = {node: i for i, node in enumerate(nodes)}
    matrix = [[0.0 for _ in nodes] for _ in nodes]
    for a, b in edges:
        if a in index and b in index and a != b:
            i, j = index[a], index[b]
            matrix[i][j] = float(hopping)
            matrix[j][i] = float(hopping)
    return matrix


def gershgorin_bounds(matrix: Sequence[Sequence[float]]) -> tuple[float, float]:
    if not matrix:
        return 0.0, 0.0
    lows = []
    highs = []
    for i, row in enumerate(matrix):
        center = float(row[i])
        radius = sum(abs(float(value)) for j, value in enumerate(row) if j != i)
        lows.append(center - radius)
        highs.append(center + radius)
    return min(lows), max(highs)


def inverse_participation_ratio(vector: Sequence[float]) -> float:
    norm2 = sum(float(x) * float(x) for x in vector)
    if norm2 <= 0:
        raise ValueError("vector must have non-zero norm")
    return sum((float(x) * float(x)) ** 2 for x in vector) / (norm2 * norm2)


def cvcd_spectral_features(summary: SpectralSummary) -> dict[str, float]:
    n = max(summary.nodes, 1)
    e = max(summary.edges, 1)
    return {
        "edge_density_proxy": summary.edges / n,
        "triangle_density_proxy": summary.triangles / n,
        "trace_a4_per_edge": summary.trace_a4 / e,
        "average_degree": summary.average_degree,
        "degree_variance": summary.degree_variance,
    }
