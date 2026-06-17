"""Minimal Omega-TFTS geometry generator.

This is not a proof of superconductivity. It is a small, executable seed for the
Omega-TFTS module: generate Cantor/Menger fractal masks and estimate graph
connectivity plus the graph cycle rank.

Run:
    python examples/omega_tfts_minimal.py
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from math import log
from typing import Iterable


Coord = tuple[int, int, int]


def ternary_digits(x: int, n: int) -> list[int]:
    """Return exactly n ternary digits, least-significant first."""
    digits: list[int] = []
    for _ in range(n):
        digits.append(x % 3)
        x //= 3
    return digits


def in_cantor_cube(coord: Coord, n: int) -> bool:
    """Cantor sparse skeleton K_n: every digit of x,y,z is in {0,2}."""
    return all(d in (0, 2) for value in coord for d in ternary_digits(value, n))


def in_menger_support(coord: Coord, n: int) -> bool:
    """Menger support M_n: at most one coordinate digit equals 1 per scale."""
    xs, ys, zs = (ternary_digits(value, n) for value in coord)
    return all((xs[i] == 1) + (ys[i] == 1) + (zs[i] == 1) <= 1 for i in range(n))


def active_voxels(n: int, kind: str) -> set[Coord]:
    """Generate active voxels for 'cantor' or 'menger'."""
    size = 3**n
    if kind == "cantor":
        predicate = in_cantor_cube
    elif kind == "menger":
        predicate = in_menger_support
    else:
        raise ValueError("kind must be 'cantor' or 'menger'")

    return {
        (x, y, z)
        for x, y, z in product(range(size), repeat=3)
        if predicate((x, y, z), n)
    }


def neighbors6(coord: Coord) -> Iterable[Coord]:
    """6-neighborhood for face-connected voxels."""
    x, y, z = coord
    yield (x + 1, y, z)
    yield (x - 1, y, z)
    yield (x, y + 1, z)
    yield (x, y - 1, z)
    yield (x, y, z + 1)
    yield (x, y, z - 1)


@dataclass(frozen=True)
class GraphSummary:
    n: int
    kind: str
    box_size: int
    voxels: int
    edges: int
    components: int
    cycle_rank: int
    density: float
    fractal_dimension_theory: float | None


def graph_summary(voxels: set[Coord], n: int, kind: str) -> GraphSummary:
    """Compute graph components and graph cycle rank E - V + C."""
    seen: set[Coord] = set()
    components = 0
    edge_count_twice = 0

    for v in voxels:
        for w in neighbors6(v):
            if w in voxels:
                edge_count_twice += 1

    edges = edge_count_twice // 2

    for start in voxels:
        if start in seen:
            continue
        components += 1
        queue: deque[Coord] = deque([start])
        seen.add(start)

        while queue:
            v = queue.popleft()
            for w in neighbors6(v):
                if w in voxels and w not in seen:
                    seen.add(w)
                    queue.append(w)

    cycle_rank = edges - len(voxels) + components
    box_size = 3**n
    if kind == "cantor":
        dim = log(8) / log(3)
    elif kind == "menger":
        dim = log(20) / log(3)
    else:
        dim = None

    return GraphSummary(
        n=n,
        kind=kind,
        box_size=box_size,
        voxels=len(voxels),
        edges=edges,
        components=components,
        cycle_rank=cycle_rank,
        density=len(voxels) / (box_size**3),
        fractal_dimension_theory=dim,
    )


def main() -> None:
    for n in range(1, 4):
        for kind in ("cantor", "menger"):
            voxels = active_voxels(n, kind)
            print(graph_summary(voxels, n, kind))


if __name__ == "__main__":
    main()
