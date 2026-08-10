from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, List, Sequence


def _solve_linear_system(matrix: List[List[float]], vector: List[float]) -> List[float]:
    """Gaussian elimination with partial pivoting for small benchmark systems."""

    n = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular design matrix; increase ridge or reduce features")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                current - factor * reference
                for current, reference in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(n)]


@dataclass(frozen=True)
class LinearModel:
    intercept: float
    coefficients: tuple[float, ...]

    def predict(self, features: Sequence[float]) -> float:
        if len(features) != len(self.coefficients):
            raise ValueError("feature dimension mismatch")
        return self.intercept + sum(weight * value for weight, value in zip(self.coefficients, features))


def fit_ridge(
    features: Sequence[Sequence[float]],
    targets: Sequence[float],
    *,
    ridge: float = 1e-8,
) -> LinearModel:
    """Fit a tiny ridge linear model without third-party numerical packages."""

    if not features or len(features) != len(targets):
        raise ValueError("features and targets must be non-empty and aligned")
    width = len(features[0])
    if any(len(row) != width for row in features):
        raise ValueError("all feature rows must have equal width")
    if ridge < 0 or not isfinite(ridge):
        raise ValueError("ridge must be finite and >= 0")

    design = [[1.0, *map(float, row)] for row in features]
    dimension = width + 1
    gram = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    rhs = [0.0 for _ in range(dimension)]
    for row, target in zip(design, targets):
        if not isfinite(target) or any(not isfinite(value) for value in row):
            raise ValueError("training data must be finite")
        for i in range(dimension):
            rhs[i] += row[i] * target
            for j in range(dimension):
                gram[i][j] += row[i] * row[j]
    for index in range(1, dimension):
        gram[index][index] += ridge

    solved = _solve_linear_system(gram, rhs)
    return LinearModel(intercept=solved[0], coefficients=tuple(solved[1:]))


def mean_squared_error(model: LinearModel, features: Sequence[Sequence[float]], targets: Sequence[float]) -> float:
    if not features or len(features) != len(targets):
        raise ValueError("evaluation features and targets must be non-empty and aligned")
    errors = [(model.predict(row) - target) ** 2 for row, target in zip(features, targets)]
    return sum(errors) / len(errors)
