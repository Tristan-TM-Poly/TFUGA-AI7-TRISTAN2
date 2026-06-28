"""Conditioning and OAK scoring utilities for Ω-VTP-T++ v2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ResidualMetrics:
    residual_norm: float
    relative_residual: float
    max_abs_error: float


@dataclass(frozen=True)
class OAKScore:
    score: float
    relative_residual: float
    condition_number: float
    feature_count: int
    sample_count: int
    train_test_gap: float
    oak_status: str


def matrix_condition_number(matrix: np.ndarray) -> float:
    """Return 2-norm condition number, guarding degenerate matrices."""

    x = np.asarray(matrix, dtype=float)
    if x.size == 0:
        return float("inf")
    singular_values = np.linalg.svd(x, compute_uv=False)
    if singular_values.size == 0 or np.min(singular_values) <= np.finfo(float).eps:
        return float("inf")
    return float(np.max(singular_values) / np.min(singular_values))


def residual_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> ResidualMetrics:
    """Compute norm, relative norm, and max absolute residual."""

    y = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    if y.shape != pred.shape:
        raise ValueError("y_true and y_pred must have the same shape.")
    err = y - pred
    residual_norm = float(np.linalg.norm(err))
    relative = residual_norm / max(float(np.linalg.norm(y)), np.finfo(float).eps)
    max_abs = float(np.max(np.abs(err))) if err.size else 0.0
    return ResidualMetrics(residual_norm, relative, max_abs)


def oak_score(
    *,
    relative_residual: float,
    condition_number: float,
    feature_count: int,
    sample_count: int,
    train_test_gap: float = 0.0,
) -> OAKScore:
    """Compute a bounded OAK score that penalizes residual, instability and cost."""

    feature_pressure = feature_count / max(sample_count, 1)
    finite_condition = condition_number if np.isfinite(condition_number) else 1e12
    score = 1.0 / (
        (1.0 + max(relative_residual, 0.0))
        * (1.0 + max(train_test_gap, 0.0))
        * (1.0 + np.log1p(max(finite_condition, 0.0)))
        * (1.0 + max(feature_pressure, 0.0))
    )

    if relative_residual <= 1e-10 and train_test_gap <= 1e-8:
        status = "certified"
    elif relative_residual <= 1e-6 and train_test_gap <= 1e-4:
        status = "checked"
    elif relative_residual <= 1e-2:
        status = "experimental"
    else:
        status = "experimental_residual_high"

    return OAKScore(
        score=float(score),
        relative_residual=float(relative_residual),
        condition_number=float(condition_number),
        feature_count=int(feature_count),
        sample_count=int(sample_count),
        train_test_gap=float(train_test_gap),
        oak_status=status,
    )
