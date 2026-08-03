"""Pure-Python low-rank matrix factorization with explicit residuals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .linalg import Matrix, Vector, add, frobenius_norm, matvec, norm, outer, scale, subtract, transpose


@dataclass(frozen=True)
class RankOneFactor:
    singular_value: float
    left: Vector
    right: Vector

    def matrix(self) -> Matrix:
        return scale(outer(self.left, self.right), self.singular_value)


@dataclass(frozen=True)
class LowRankResult:
    factors: tuple[RankOneFactor, ...]
    approximation: Matrix
    residual: Matrix
    input_norm: float
    residual_norm: float
    captured_energy_fraction: float
    converged: bool


def _normalize_or_basis(vector: Sequence[float], fallback_index: int = 0) -> Vector:
    length = norm(vector)
    if length <= 1e-15:
        return tuple(1.0 if index == fallback_index else 0.0 for index in range(len(vector)))
    return tuple(float(value) / length for value in vector)


def dominant_rank_one(
    matrix: Matrix,
    *,
    iterations: int = 128,
    tolerance: float = 1e-12,
) -> tuple[RankOneFactor, bool]:
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if rows == 0 or cols == 0 or any(len(row) != cols for row in matrix):
        raise ValueError("matrix must be non-empty and rectangular")
    right = _normalize_or_basis(
        tuple(1.0 + index / max(cols, 1) for index in range(cols))
    )
    converged = False
    for _ in range(iterations):
        left_raw = matvec(matrix, right)
        left = _normalize_or_basis(left_raw)
        right_raw = matvec(transpose(matrix), left)
        next_right = _normalize_or_basis(right_raw)
        delta = norm(tuple(a - b for a, b in zip(next_right, right, strict=True)))
        right = next_right
        if delta <= tolerance:
            converged = True
            break
    left_raw = matvec(matrix, right)
    sigma = norm(left_raw)
    left = _normalize_or_basis(left_raw)
    if sigma <= tolerance:
        sigma = 0.0
    return RankOneFactor(sigma, left, right), converged


def low_rank_approximation(
    matrix: Matrix,
    rank: int,
    *,
    iterations: int = 128,
    tolerance: float = 1e-12,
) -> LowRankResult:
    if rank < 0:
        raise ValueError("rank must be non-negative")
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if rows == 0 or cols == 0 or any(len(row) != cols for row in matrix):
        raise ValueError("matrix must be non-empty and rectangular")
    residual = matrix
    approximation = tuple(tuple(0.0 for _ in range(cols)) for _ in range(rows))
    factors = []
    all_converged = True
    for _ in range(min(rank, rows, cols)):
        factor, converged = dominant_rank_one(
            residual,
            iterations=iterations,
            tolerance=tolerance,
        )
        all_converged = all_converged and converged
        if factor.singular_value <= tolerance:
            break
        component = factor.matrix()
        approximation = add(approximation, component)
        residual = subtract(matrix, approximation)
        factors.append(factor)
    input_norm = frobenius_norm(matrix)
    residual_norm = frobenius_norm(residual)
    captured = (
        1.0
        if input_norm <= tolerance
        else max(0.0, 1.0 - (residual_norm / input_norm) ** 2)
    )
    return LowRankResult(
        factors=tuple(factors),
        approximation=approximation,
        residual=residual,
        input_norm=input_norm,
        residual_norm=residual_norm,
        captured_energy_fraction=captured,
        converged=all_converged,
    )
