"""Train/test OAK validation for TensorProd Koopman fits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .conditioning import OAKScore, oak_score, residual_metrics
from .koopman_tensorprod import fit_koopman_tensorprod, predict_lifted, _resolve_lift
from .tensor_prod_lift import LiftResult


@dataclass(frozen=True)
class TrainTestOAKReport:
    degree: int
    basis: str
    train_relative_residual: float
    test_relative_residual: float
    train_test_gap: float
    score: OAKScore
    train_count: int
    test_count: int
    feature_count: int


def train_test_koopman_oak(
    x_samples: Sequence[Sequence[float]] | np.ndarray,
    y_samples: Sequence[Sequence[float]] | np.ndarray,
    *,
    degree: int,
    lift: str | Callable[..., LiftResult] = "monomial",
    test_fraction: float = 0.25,
    seed: int = 0,
) -> TrainTestOAKReport:
    """Fit on train samples and measure lifted residual on test samples."""

    x = np.asarray(x_samples, dtype=float)
    y = np.asarray(y_samples, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    if x.shape != y.shape:
        raise ValueError("x_samples and y_samples must have the same shape.")
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be in (0, 1).")

    n = x.shape[0]
    rng = np.random.default_rng(seed)
    indices = np.arange(n)
    rng.shuffle(indices)
    test_count = max(1, int(round(n * test_fraction)))
    test_idx = indices[:test_count]
    train_idx = indices[test_count:]
    if train_idx.size == 0:
        raise ValueError("not enough samples for a train split.")

    fit = fit_koopman_tensorprod(x[train_idx], y[train_idx], degree=degree, lift=lift)
    lift_fn = _resolve_lift(lift)

    train_pred = predict_lifted(fit, x[train_idx])
    test_pred = predict_lifted(fit, x[test_idx])
    train_true = lift_fn(y[train_idx], degree).features
    test_true = lift_fn(y[test_idx], degree).features

    train_res = residual_metrics(train_true, train_pred)
    test_res = residual_metrics(test_true, test_pred)
    gap = max(0.0, test_res.relative_residual - train_res.relative_residual)
    score = oak_score(
        relative_residual=test_res.relative_residual,
        condition_number=fit.fit.report.condition_number,
        feature_count=fit.fit.report.feature_count,
        sample_count=train_idx.size,
        train_test_gap=gap,
    )

    return TrainTestOAKReport(
        degree=degree,
        basis=fit.basis,
        train_relative_residual=train_res.relative_residual,
        test_relative_residual=test_res.relative_residual,
        train_test_gap=gap,
        score=score,
        train_count=int(train_idx.size),
        test_count=int(test_idx.size),
        feature_count=int(fit.fit.report.feature_count),
    )
