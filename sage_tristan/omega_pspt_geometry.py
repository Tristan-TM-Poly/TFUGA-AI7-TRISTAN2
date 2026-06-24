"""Geometry and graph utilities for Omega-PSPT++.

This module is intentionally dependency-light. It gives the repository an
executable starting point for fractal/hyperloop solid-phase prototypes without
requiring NumPy, NetworkX, or external solvers.

The functions here are not experimental claims. They are scaffolding for OAK-1
and OAK-2 work: generate lattices, count connectivity, compute cycle rank,
and prepare data for future transport/topology/LC-RLC simulations.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Sequence, Set, Tuple

Point2D = Tuple[int, int]
Point3D = Tuple[int, int, int]
Edge2D = Tuple[Point2D, Point2D]
Edge3D = Tuple[Point3D, Point3D]


@dataclass(frozen=True)
class GraphSummary:
    """Small graph summary used as a phase-geometry invariant."""

    vertices: int
    edges: int
    components: int
    cycle_rank: int
    boundary_vertices: int
    average_degree: float


@dataclass(frozen=True)
class FractalSummary:
    """Compact descriptor for generated fractal supports."""

    name: str
    iteration: int
    dimension_embedding: int
    occupied_sites: int
    bounding_size: int
    graph: GraphSummary
    estimated_fractal_dimension: float | None = None


def cantor_word(iteration: int, keep: Sequence[int] = (1, 0, 1)) -> List[int]:
    """Return the 1D Cantor-like occupancy word after ``iteration`` steps.

    ``keep=(1,0,1)`` gives the classic middle-third construction encoded as
    occupied/removed cells.
    """

    if iteration < 0:
        raise ValueError("iteration must be non-negative")
    if not keep or any(bit not in (0, 1) for bit in keep):
        raise ValueError("keep must be a non-empty 0/1 sequence")
    word = [1]
    for _ in range(iteration):
        word = [bit * k for bit in word for k in keep]
    return word


def cantor_product_points(iteration: int, dims: int = 2) -> Set[Tuple[int, ...]]:
    """Return occupied points of a Cartesian product Cantor support."""

    if dims <= 0:
        raise ValueError("dims must be positive")
    word = cantor_word(iteration)
    occupied_axes = [i for i, bit in enumerate(word) if bit]
    points: Set[Tuple[int, ...]] = {()}
    for _ in range(dims):
        points = {prefix + (axis,) for prefix in points for axis in occupied_axes}
    return points


def sierpinski_carpet_points(iteration: int) -> Set[Point2D]:
    """Return occupied cells for a Sierpinski-carpet-like 2D lattice."""

    if iteration < 0:
        raise ValueError("iteration must be non-negative")
    points: Set[Point2D] = {(0, 0)}
    for _ in range(iteration):
        new_points: Set[Point2D] = set()
        for x, y in points:
            for dx in range(3):
                for dy in range(3):
                    if (dx, dy) == (1, 1):
                        continue
                    new_points.add((3 * x + dx, 3 * y + dy))
        points = new_points
    return points


def menger_sponge_points(iteration: int) -> Set[Point3D]:
    """Return occupied cells for a Menger-sponge-like 3D lattice."""

    if iteration < 0:
        raise ValueError("iteration must be non-negative")
    points: Set[Point3D] = {(0, 0, 0)}
    for _ in range(iteration):
        new_points: Set[Point3D] = set()
        for x, y, z in points:
            for dx in range(3):
                for dy in range(3):
                    for dz in range(3):
                        centered_axes = sum(coord == 1 for coord in (dx, dy, dz))
                        if centered_axes >= 2:
                            continue
                        new_points.add((3 * x + dx, 3 * y + dy, 3 * z + dz))
        points = new_points
    return points


def nearest_neighbor_edges(points: Iterable[Tuple[int, ...]]) -> Set[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    """Return axis-aligned nearest-neighbor edges between occupied lattice cells."""

    point_set = set(points)
    if not point_set:
        return set()
    dims = len(next(iter(point_set)))
    edges: Set[Tuple[Tuple[int, ...], Tuple[int, ...]]] = set()
    for point in point_set:
        for axis in range(dims):
            neighbor = list(point)
            neighbor[axis] += 1
            neighbor_tuple = tuple(neighbor)
            if neighbor_tuple in point_set:
                edges.add((point, neighbor_tuple) if point < neighbor_tuple else (neighbor_tuple, point))
    return edges


def connected_components(points: Iterable[Tuple[int, ...]], edges: Iterable[Tuple[Tuple[int, ...], Tuple[int, ...]]]) -> List[Set[Tuple[int, ...]]]:
    """Return connected components for an undirected graph."""

    point_set = set(points)
    adjacency: Dict[Tuple[int, ...], Set[Tuple[int, ...]]] = {p: set() for p in point_set}
    for a, b in edges:
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    components: List[Set[Tuple[int, ...]]] = []
    seen: Set[Tuple[int, ...]] = set()
    for start in point_set:
        if start in seen:
            continue
        comp: Set[Tuple[int, ...]] = set()
        queue: deque[Tuple[int, ...]] = deque([start])
        seen.add(start)
        while queue:
            node = queue.popleft()
            comp.add(node)
            for nxt in adjacency.get(node, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(comp)
    return components


def boundary_vertices(points: Iterable[Tuple[int, ...]]) -> Set[Tuple[int, ...]]:
    """Return occupied sites on the bounding-box boundary."""

    point_set = set(points)
    if not point_set:
        return set()
    dims = len(next(iter(point_set)))
    mins = [min(p[axis] for p in point_set) for axis in range(dims)]
    maxs = [max(p[axis] for p in point_set) for axis in range(dims)]
    return {
        p
        for p in point_set
        if any(p[axis] == mins[axis] or p[axis] == maxs[axis] for axis in range(dims))
    }


def summarize_graph(points: Iterable[Tuple[int, ...]]) -> GraphSummary:
    """Summarize nearest-neighbor graph invariants for a point support."""

    point_set = set(points)
    edges = nearest_neighbor_edges(point_set)
    components = connected_components(point_set, edges)
    v = len(point_set)
    e = len(edges)
    c = len(components)
    beta_1 = max(0, e - v + c)
    avg_degree = (2.0 * e / v) if v else 0.0
    return GraphSummary(
        vertices=v,
        edges=e,
        components=c,
        cycle_rank=beta_1,
        boundary_vertices=len(boundary_vertices(point_set)),
        average_degree=avg_degree,
    )


def summarize_fractal(name: str, iteration: int) -> FractalSummary:
    """Generate a named fractal and return compact invariants."""

    import math

    normalized = name.strip().lower().replace("-", "_")
    if normalized in {"cantor2", "cantor_2d", "cantor_product_2d"}:
        points = cantor_product_points(iteration, dims=2)
        embedded = 2
        estimated = 2.0 * math.log(2.0) / math.log(3.0) if iteration > 0 else None
    elif normalized in {"cantor3", "cantor_3d", "cantor_product_3d"}:
        points = cantor_product_points(iteration, dims=3)
        embedded = 3
        estimated = 3.0 * math.log(2.0) / math.log(3.0) if iteration > 0 else None
    elif normalized in {"sierpinski", "sierpinski_carpet"}:
        points = sierpinski_carpet_points(iteration)
        embedded = 2
        estimated = math.log(8.0) / math.log(3.0) if iteration > 0 else None
    elif normalized in {"menger", "menger_sponge"}:
        points = menger_sponge_points(iteration)
        embedded = 3
        estimated = math.log(20.0) / math.log(3.0) if iteration > 0 else None
    else:
        raise ValueError(f"Unknown fractal name: {name}")

    bounding_size = 3**iteration if iteration > 0 else 1
    return FractalSummary(
        name=normalized,
        iteration=iteration,
        dimension_embedding=embedded,
        occupied_sites=len(points),
        bounding_size=bounding_size,
        graph=summarize_graph(points),
        estimated_fractal_dimension=estimated,
    )


def ascii_plot_2d(points: Iterable[Point2D], occupied: str = "#", empty: str = ".") -> str:
    """Render a small 2D support as ASCII for docs/debugging."""

    point_set = set(points)
    if not point_set:
        return ""
    max_x = max(x for x, _ in point_set)
    max_y = max(y for _, y in point_set)
    rows = []
    for y in range(max_y, -1, -1):
        rows.append("".join(occupied if (x, y) in point_set else empty for x in range(max_x + 1)))
    return "\n".join(rows)
