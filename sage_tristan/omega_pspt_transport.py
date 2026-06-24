"""Transport utilities for Omega-PSPT++.

This module adds a dependency-free resistor-network layer for OAK-2 prototypes.
It is designed for small generated lattices first: enough to compare fractal,
random, and control geometries before moving to optimized numerical solvers.

Scientific discipline:
- geometry-to-conductance claims must be compared against matched controls;
- effective resistance is a model descriptor, not an experimental result;
- contact choice is part of the claim and must be made explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

Node = Tuple[int, ...]
Edge = Tuple[Node, Node]


@dataclass(frozen=True)
class TransportSummary:
    """Compact transport descriptor for a resistor network."""

    source: Node
    sink: Node
    effective_resistance: float
    effective_conductance: float
    nodes: int
    edges: int
    grounded_nodes: int


def canonical_edge(a: Node, b: Node) -> Edge:
    """Return a stable undirected edge tuple."""

    return (a, b) if a <= b else (b, a)


def adjacency_from_edges(edges: Iterable[Edge]) -> Dict[Node, Dict[Node, float]]:
    """Build weighted adjacency using conductance values.

    Duplicate edges add conductance in parallel.
    """

    adjacency: Dict[Node, Dict[Node, float]] = {}
    for a, b in edges:
        if a == b:
            continue
        adjacency.setdefault(a, {})[b] = adjacency.setdefault(a, {}).get(b, 0.0) + 1.0
        adjacency.setdefault(b, {})[a] = adjacency.setdefault(b, {}).get(a, 0.0) + 1.0
    return adjacency


def weighted_adjacency_from_resistances(edge_resistance: Mapping[Edge, float]) -> Dict[Node, Dict[Node, float]]:
    """Build adjacency from edge resistances.

    Conductance is 1/R. Duplicate canonical edges are not expected in the map.
    """

    adjacency: Dict[Node, Dict[Node, float]] = {}
    for edge, resistance in edge_resistance.items():
        if resistance <= 0:
            raise ValueError("edge resistances must be positive")
        a, b = canonical_edge(*edge)
        if a == b:
            continue
        conductance = 1.0 / resistance
        adjacency.setdefault(a, {})[b] = adjacency.setdefault(a, {}).get(b, 0.0) + conductance
        adjacency.setdefault(b, {})[a] = adjacency.setdefault(b, {}).get(a, 0.0) + conductance
    return adjacency


def laplacian(adjacency: Mapping[Node, Mapping[Node, float]], nodes: Sequence[Node]) -> List[List[float]]:
    """Return the weighted graph Laplacian in the supplied node order."""

    index = {node: i for i, node in enumerate(nodes)}
    matrix = [[0.0 for _ in nodes] for _ in nodes]
    for node, neighbors in adjacency.items():
        i = index[node]
        total = 0.0
        for neighbor, conductance in neighbors.items():
            j = index[neighbor]
            total += conductance
            matrix[i][j] -= conductance
        matrix[i][i] += total
    return matrix


def solve_linear_system(matrix: List[List[float]], rhs: List[float]) -> List[float]:
    """Solve a dense linear system with Gaussian elimination.

    This tiny solver is intended for small OAK-2 prototypes. For large lattices,
    replace with NumPy/SciPy sparse solvers.
    """

    n = len(rhs)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square and match rhs length")
    a = [row[:] + [float(rhs_i)] for row, rhs_i in zip(matrix, rhs)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("singular network matrix; check source/sink connectivity")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]

        pivot_value = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= pivot_value

        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if abs(factor) < 1e-18:
                continue
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]


def effective_resistance(
    edges: Iterable[Edge],
    source: Node,
    sink: Node,
    edge_resistance: Mapping[Edge, float] | None = None,
) -> float:
    """Compute effective resistance between ``source`` and ``sink``.

    A unit current is injected at source and extracted at sink. The sink is
    grounded, and the source voltage equals the effective resistance.
    """

    edge_list = [canonical_edge(*edge) for edge in edges]
    nodes = sorted({node for edge in edge_list for node in edge})
    if source not in nodes or sink not in nodes:
        raise ValueError("source and sink must exist in the edge set")
    if source == sink:
        raise ValueError("source and sink must differ")

    if edge_resistance is None:
        adjacency = adjacency_from_edges(edge_list)
    else:
        canonical_resistance = {canonical_edge(*edge): value for edge, value in edge_resistance.items()}
        adjacency = weighted_adjacency_from_resistances(canonical_resistance)

    unknown_nodes = [node for node in nodes if node != sink]
    matrix_full = laplacian(adjacency, nodes)
    full_index = {node: i for i, node in enumerate(nodes)}
    unknown_index = {node: i for i, node in enumerate(unknown_nodes)}

    matrix = [[0.0 for _ in unknown_nodes] for _ in unknown_nodes]
    rhs = [0.0 for _ in unknown_nodes]
    rhs[unknown_index[source]] = 1.0

    for row_node in unknown_nodes:
        row = unknown_index[row_node]
        full_row = full_index[row_node]
        for col_node in unknown_nodes:
            col = unknown_index[col_node]
            matrix[row][col] = matrix_full[full_row][full_index[col_node]]

    voltages = solve_linear_system(matrix, rhs)
    return voltages[unknown_index[source]]


def boundary_terminals(points: Iterable[Node], axis: int = 0) -> Tuple[List[Node], List[Node]]:
    """Return min-axis and max-axis boundary terminal sets."""

    point_set = set(points)
    if not point_set:
        raise ValueError("points cannot be empty")
    min_value = min(point[axis] for point in point_set)
    max_value = max(point[axis] for point in point_set)
    left = sorted(point for point in point_set if point[axis] == min_value)
    right = sorted(point for point in point_set if point[axis] == max_value)
    return left, right


def terminal_supernode_edges(points: Iterable[Node], edges: Iterable[Edge], axis: int = 0) -> Tuple[List[Edge], Node, Node]:
    """Attach all min/max boundary sites to source/sink supernodes.

    This approximates ideal electrodes spanning opposite faces of a sample.
    """

    point_set = set(points)
    left, right = boundary_terminals(point_set, axis=axis)
    source = (-(axis + 1),)
    sink = (axis + 1,)
    augmented = [canonical_edge(*edge) for edge in edges]
    augmented.extend(canonical_edge(source, node) for node in left)
    augmented.extend(canonical_edge(node, sink) for node in right)
    return augmented, source, sink


def summarize_transport(points: Iterable[Node], edges: Iterable[Edge], axis: int = 0) -> TransportSummary:
    """Compute face-to-face effective resistance with idealized electrodes."""

    point_set = set(points)
    edge_list = [canonical_edge(*edge) for edge in edges]
    augmented, source, sink = terminal_supernode_edges(point_set, edge_list, axis=axis)
    resistance = effective_resistance(augmented, source, sink)
    conductance = 1.0 / resistance if resistance > 0 else float("inf")
    return TransportSummary(
        source=source,
        sink=sink,
        effective_resistance=resistance,
        effective_conductance=conductance,
        nodes=len(point_set),
        edges=len(edge_list),
        grounded_nodes=2,
    )


def normalized_conductance_score(summary: TransportSummary, occupied_sites: int, bounding_size: int) -> float:
    """Return a simple normalized conductance descriptor.

    This is not a universal physical normalization. It is a compact comparison
    feature for matched-control OAK experiments.
    """

    if occupied_sites <= 0 or bounding_size <= 0:
        raise ValueError("occupied_sites and bounding_size must be positive")
    fill_fraction = occupied_sites / float(bounding_size)
    return summary.effective_conductance / max(fill_fraction, 1e-12)
