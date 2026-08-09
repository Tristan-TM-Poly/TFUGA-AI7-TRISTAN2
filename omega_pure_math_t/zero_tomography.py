"""Finite log-potential sampler for Ω-ZERO-TOMOGRAPHY-T∞.

This is a numerical laboratory, not a zero-certification algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, pi
from typing import Callable, Iterable


@dataclass(frozen=True)
class Grid:
    xs: tuple[float, ...]
    ys: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]


def log_modulus_grid(
    function: Callable[[complex], complex],
    xs: Iterable[float],
    ys: Iterable[float],
    *,
    floor: float = 1e-300,
) -> Grid:
    if floor <= 0:
        raise ValueError("floor must be positive")
    x_values = tuple(float(x) for x in xs)
    y_values = tuple(float(y) for y in ys)
    if len(x_values) < 3 or len(y_values) < 3:
        raise ValueError("need at least a 3x3 grid")
    rows = tuple(
        tuple(log(max(abs(function(complex(x, y))), floor)) for x in x_values)
        for y in y_values
    )
    return Grid(x_values, y_values, rows)


def discrete_laplacian(grid: Grid) -> Grid:
    """Five-point Laplacian for a uniform rectangular grid; boundary is NaN."""

    if len(grid.xs) < 3 or len(grid.ys) < 3:
        raise ValueError("need at least a 3x3 grid")
    hx = grid.xs[1] - grid.xs[0]
    hy = grid.ys[1] - grid.ys[0]
    if hx == 0 or hy == 0:
        raise ValueError("grid spacing must be non-zero")
    tolerance = 1e-12
    if any(abs((grid.xs[i + 1] - grid.xs[i]) - hx) > tolerance for i in range(len(grid.xs) - 1)):
        raise ValueError("xs must be uniformly spaced")
    if any(abs((grid.ys[i + 1] - grid.ys[i]) - hy) > tolerance for i in range(len(grid.ys) - 1)):
        raise ValueError("ys must be uniformly spaced")

    rows: list[tuple[float, ...]] = []
    for j in range(len(grid.ys)):
        row: list[float] = []
        for i in range(len(grid.xs)):
            if i in {0, len(grid.xs) - 1} or j in {0, len(grid.ys) - 1}:
                row.append(float("nan"))
                continue
            center = grid.values[j][i]
            dxx = (grid.values[j][i + 1] - 2 * center + grid.values[j][i - 1]) / (hx * hx)
            dyy = (grid.values[j + 1][i] - 2 * center + grid.values[j - 1][i]) / (hy * hy)
            row.append(dxx + dyy)
        rows.append(tuple(row))
    return Grid(grid.xs, grid.ys, tuple(rows))


def source_density(grid: Grid) -> Grid:
    """Return the discrete diagnostic rho=Delta(log|f|)/(2*pi)."""

    lap = discrete_laplacian(grid)
    return Grid(
        lap.xs,
        lap.ys,
        tuple(tuple(value / (2 * pi) for value in row) for row in lap.values),
    )


def strongest_interior_sources(grid: Grid, count: int = 1) -> tuple[tuple[complex, float], ...]:
    """Return the largest finite *positive* interior source-density samples.

    Negative samples are not silently relabeled as zero sources; in meromorphic
    settings they can instead carry pole-like information and should be handled
    by a separate signed-source analysis.
    """

    from math import isfinite

    if count < 1:
        raise ValueError("count must be >=1")
    candidates: list[tuple[float, complex]] = []
    for j, y in enumerate(grid.ys):
        for i, x in enumerate(grid.xs):
            value = grid.values[j][i]
            if isfinite(value) and value > 0:
                candidates.append((value, complex(x, y)))
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return tuple((point, value) for value, point in candidates[:count])
