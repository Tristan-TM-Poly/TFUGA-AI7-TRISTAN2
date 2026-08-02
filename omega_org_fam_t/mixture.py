"""Dependency-free non-negative mixture fitting for spectral feature vectors."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class MixtureFit:
    coefficients: dict[str, float]
    reconstruction: tuple[float, ...]
    residual: tuple[float, ...]
    rmse: float
    iterations: int
    converged: bool


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def fit_nonnegative_mixture(
    observed: Sequence[float],
    references: Mapping[str, Sequence[float]],
    *,
    max_iter: int = 2_000,
    tolerance: float = 1e-10,
    l1_penalty: float = 0.0,
) -> MixtureFit:
    names = tuple(sorted(references))
    if not names:
        raise ValueError("at least one reference is required")
    dimension = len(observed)
    if dimension == 0 or any(len(references[name]) != dimension for name in names):
        raise ValueError("all vectors must have the same non-zero dimension")
    if any(value < 0 for value in observed) or any(value < 0 for name in names for value in references[name]):
        raise ValueError("spectral intensities must be non-negative")
    if max_iter <= 0 or tolerance < 0 or l1_penalty < 0:
        raise ValueError("invalid solver settings")
    columns = [tuple(float(value) for value in references[name]) for name in names]
    norms = [_dot(column, column) for column in columns]
    coefficients = [0.0] * len(names)
    reconstruction = [0.0] * dimension
    converged = False
    iteration = 0
    for iteration in range(1, max_iter + 1):
        max_delta = 0.0
        for column_index, column in enumerate(columns):
            norm = norms[column_index]
            if norm == 0:
                continue
            old = coefficients[column_index]
            correlation = sum(column[i] * (observed[i] - reconstruction[i] + old * column[i]) for i in range(dimension))
            new = max(0.0, (correlation - l1_penalty) / norm)
            delta = new - old
            if delta:
                coefficients[column_index] = new
                for i in range(dimension):
                    reconstruction[i] += delta * column[i]
                max_delta = max(max_delta, abs(delta))
        if max_delta <= tolerance:
            converged = True
            break
    residual = tuple(float(observed[i]) - reconstruction[i] for i in range(dimension))
    rmse = sqrt(sum(value * value for value in residual) / dimension)
    return MixtureFit(
        coefficients={name: round(coefficients[index], 12) for index, name in enumerate(names)},
        reconstruction=tuple(round(value, 12) for value in reconstruction),
        residual=tuple(round(value, 12) for value in residual),
        rmse=round(rmse, 12),
        iterations=iteration,
        converged=converged,
    )
