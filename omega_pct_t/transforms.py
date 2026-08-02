from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import fmean
from typing import Iterable, Sequence


@dataclass(frozen=True)
class HaarLevel:
    approximation: tuple[float, ...]
    detail: tuple[float, ...]


def _pad_even(values: Sequence[float]) -> list[float]:
    data = list(map(float, values))
    if len(data) % 2:
        data.append(data[-1] if data else 0.0)
    return data


def haar_decompose(values: Sequence[float], levels: int | None = None) -> list[HaarLevel]:
    data = _pad_even(values)
    result: list[HaarLevel] = []
    max_levels = levels if levels is not None else 10**9
    while len(data) >= 2 and len(result) < max_levels:
        approximation: list[float] = []
        detail: list[float] = []
        for index in range(0, len(data), 2):
            left, right = data[index], data[index + 1]
            approximation.append((left + right) / sqrt(2.0))
            detail.append((left - right) / sqrt(2.0))
        result.append(HaarLevel(tuple(approximation), tuple(detail)))
        if len(approximation) == 1:
            break
        data = _pad_even(approximation)
    return result


def haar_reconstruct(levels: Sequence[HaarLevel], original_length: int | None = None) -> list[float]:
    if not levels:
        return []
    current = list(levels[-1].approximation)
    for level in reversed(levels):
        if len(current) != len(level.detail):
            current = list(level.approximation)
        rebuilt: list[float] = []
        for approximation, detail in zip(current, level.detail):
            rebuilt.extend(((approximation + detail) / sqrt(2.0), (approximation - detail) / sqrt(2.0)))
        current = rebuilt
    if original_length is not None:
        current = current[:original_length]
    return current


def ffwt_features(values: Sequence[float]) -> dict[str, float | list[float]]:
    levels = haar_decompose(values)
    energies = [sum(value * value for value in level.detail) for level in levels]
    total = sum(energies)
    normalized = [value / total if total else 0.0 for value in energies]
    persistence = 0.0
    if len(normalized) > 1:
        persistence = sum(min(normalized[i], normalized[i + 1]) for i in range(len(normalized) - 1))
    sparsity = 0.0
    coefficients = [abs(value) for level in levels for value in level.detail]
    if coefficients:
        threshold = fmean(coefficients)
        sparsity = sum(value < threshold for value in coefficients) / len(coefficients)
    return {"detail_energy": energies, "normalized_energy": normalized, "cross_scale_persistence": persistence, "below_mean_fraction": sparsity}


def residual_multiscale_score(observed: Sequence[float], expected: Sequence[float]) -> dict[str, float | list[float]]:
    if len(observed) != len(expected):
        raise ValueError("observed and expected must have equal lengths")
    residuals = [float(a) - float(b) for a, b in zip(observed, expected)]
    features = ffwt_features(residuals)
    features["l2"] = sqrt(sum(value * value for value in residuals))
    features["max_abs"] = max((abs(value) for value in residuals), default=0.0)
    return features
