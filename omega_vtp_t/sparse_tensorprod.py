"""Sparse/CVCD TensorProd selection for Ω-VTP-T++.

The full TensorProd lift grows as C(n + J, J). This module adds a first
OAK-safe selection layer: keep only features that are numerically useful,
stable, and not dominated by memory cost.

This is deliberately simple: it is a baseline for future CVCD selection, not a
claim of optimal sparsity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

from .tensor_prod_lift import Alpha, LiftResult, tensor_prod_lift


@dataclass(frozen=True)
class SparseSelectionReport:
    """Report for sparse feature selection."""

    original_feature_count: int
    selected_feature_count: int
    threshold: float
    method: str
    oak_status: str


@dataclass(frozen=True)
class SparseLiftResult:
    """Sparse TensorProd result with selected feature labels."""

    features: np.ndarray
    alphas: Tuple[Alpha, ...]
    selected_indices: Tuple[int, ...]
    report: SparseSelectionReport


def select_by_variance(
    lift: LiftResult,
    *,
    threshold: float = 1e-12,
    keep_constant: bool = True,
) -> SparseLiftResult:
    """Keep lifted features with variance above a threshold.

    Constant features are useful for polynomial intercepts, so the alpha=(0,...,0)
    feature can be retained even though its variance is zero.
    """

    features = np.asarray(lift.features, dtype=float)
    if features.ndim != 2:
        raise ValueError("lift.features must be a 2D matrix.")

    variances = np.var(features, axis=0)
    selected = []
    zero_alpha = tuple(0 for _ in lift.alphas[0]) if lift.alphas else ()

    for idx, (alpha, variance) in enumerate(zip(lift.alphas, variances)):
        if keep_constant and alpha == zero_alpha:
            selected.append(idx)
        elif variance > threshold:
            selected.append(idx)

    if not selected and features.shape[1] > 0:
        selected = [int(np.argmax(variances))]

    selected_tuple = tuple(int(i) for i in selected)
    selected_features = features[:, selected_tuple]
    selected_alphas = tuple(lift.alphas[i] for i in selected_tuple)

    status = "checked" if len(selected_tuple) <= features.shape[1] else "failed"
    return SparseLiftResult(
        features=selected_features,
        alphas=selected_alphas,
        selected_indices=selected_tuple,
        report=SparseSelectionReport(
            original_feature_count=features.shape[1],
            selected_feature_count=len(selected_tuple),
            threshold=threshold,
            method="variance_threshold",
            oak_status=status,
        ),
    )


def select_by_correlation_with_target(
    lift: LiftResult,
    target: Sequence[float] | np.ndarray,
    *,
    top_k: int,
    keep_constant: bool = True,
) -> SparseLiftResult:
    """Keep the features most correlated with a scalar target.

    This is a first CVCD-like fertility score:
        fertile(feature) ≈ |corr(feature, target)|

    It is useful for regression discovery, but must be cross-validated before
    claiming causal or predictive value.
    """

    features = np.asarray(lift.features, dtype=float)
    y = np.asarray(target, dtype=float).reshape(-1)
    if features.shape[0] != y.shape[0]:
        raise ValueError("target length must match sample count.")
    if top_k < 1:
        raise ValueError("top_k must be >= 1.")

    centered_x = features - np.mean(features, axis=0, keepdims=True)
    centered_y = y - np.mean(y)
    denom = np.linalg.norm(centered_x, axis=0) * max(np.linalg.norm(centered_y), np.finfo(float).eps)
    scores = np.divide(
        np.abs(centered_x.T @ centered_y),
        denom,
        out=np.zeros(features.shape[1]),
        where=denom > 0,
    )

    selected = set(np.argsort(scores)[-min(top_k, features.shape[1]) :].tolist())
    if keep_constant and lift.alphas:
        zero_alpha = tuple(0 for _ in lift.alphas[0])
        for idx, alpha in enumerate(lift.alphas):
            if alpha == zero_alpha:
                selected.add(idx)
                break

    selected_tuple = tuple(sorted(int(i) for i in selected))
    selected_features = features[:, selected_tuple]
    selected_alphas = tuple(lift.alphas[i] for i in selected_tuple)

    return SparseLiftResult(
        features=selected_features,
        alphas=selected_alphas,
        selected_indices=selected_tuple,
        report=SparseSelectionReport(
            original_feature_count=features.shape[1],
            selected_feature_count=len(selected_tuple),
            threshold=float(top_k),
            method="target_correlation_top_k",
            oak_status="experimental_needs_cross_validation",
        ),
    )


def sparse_tensor_prod_lift(
    samples: Sequence[Sequence[float]] | np.ndarray,
    degree: int,
    *,
    variance_threshold: float = 1e-12,
) -> SparseLiftResult:
    """Convenience wrapper: full lift followed by variance selection."""

    return select_by_variance(
        tensor_prod_lift(samples, degree),
        threshold=variance_threshold,
        keep_constant=True,
    )
