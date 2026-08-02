from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ConservationBudget:
    initial: float
    final: float
    integrated_sources: float = 0.0
    integrated_boundary_flux: float = 0.0

    @property
    def residual(self) -> float:
        return self.final - self.initial - self.integrated_sources + self.integrated_boundary_flux

    @property
    def relative_residual(self) -> float:
        scale = max(abs(self.initial), abs(self.final), 1e-30)
        return self.residual / scale

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "residual": self.residual, "relative_residual": self.relative_residual}


def integrate_1d(values: Iterable[float], dx: float) -> float:
    data = list(values)
    if dx <= 0:
        raise ValueError("dx must be positive")
    if len(data) < 2:
        return 0.0
    return dx * (0.5 * data[0] + sum(data[1:-1]) + 0.5 * data[-1])


def discrete_divergence_2d(
    u: list[list[float]],
    v: list[list[float]],
    *,
    dx: float,
    dy: float,
) -> list[list[float]]:
    if dx <= 0 or dy <= 0:
        raise ValueError("dx and dy must be positive")
    if len(u) != len(v) or not u or len(u[0]) != len(v[0]):
        raise ValueError("u and v must share a non-empty rectangular shape")
    rows, cols = len(u), len(u[0])
    if rows < 3 or cols < 3 or any(len(row) != cols for row in u + v):
        raise ValueError("fields must be rectangular and at least 3x3")
    result = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for j in range(1, rows - 1):
        for i in range(1, cols - 1):
            dudx = (u[j][i + 1] - u[j][i - 1]) / (2.0 * dx)
            dvdy = (v[j + 1][i] - v[j - 1][i]) / (2.0 * dy)
            result[j][i] = dudx + dvdy
    return result


def max_abs_interior(field: list[list[float]]) -> float:
    if len(field) < 3 or len(field[0]) < 3:
        return 0.0
    return max(
        abs(field[j][i])
        for j in range(1, len(field) - 1)
        for i in range(1, len(field[0]) - 1)
    )
