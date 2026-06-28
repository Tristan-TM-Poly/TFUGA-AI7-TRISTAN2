"""CVCD-like feature fertility scoring for TensorProd lifts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

from .tensor_prod_lift import Alpha, LiftResult


@dataclass(frozen=True)
class FeatureFertility:
    alpha: Alpha
    score: float
    variance: float
    target_correlation: float
    degree_cost: float
    oak_status: str


@dataclass(frozen=True)
class CVCDSelection:
    features: np.ndarray
    alphas: Tuple[Alpha, ...]
    selected_indices: Tuple[int, ...]
    scores: Tuple[FeatureFertility, ...]
    oak_status: str


def _safe_abs_corr(x: np.ndarray, y: np.ndarray) -> float:
    cx = x - np.mean(x)
    cy = y - np.mean(y)
    denom = np.linalg.norm(cx) * np.linalg.norm(cy)
    if denom <= np.finfo(float).eps:
        return 0.0
    return float(abs(cx @ cy) / denom)


def feature_fertility_scores(
    lift: LiftResult,
    target: Sequence[float] | np.ndarray | None = None,
    *,
    memory_penalty: float = 0.01,
) -> Tuple[FeatureFertility, ...]:
    """Score features by variance, target correlation, and degree cost."""

    x = np.asarray(lift.features, dtype=float)
    y = None if target is None else np.asarray(target, dtype=float).reshape(-1)
    if y is not None and y.shape[0] != x.shape[0]:
        raise ValueError("target length must match sample count.")

    variances = np.var(x, axis=0)
    max_var = max(float(np.max(variances)), np.finfo(float).eps)
    out = []

    for idx, alpha in enumerate(lift.alphas):
        normalized_variance = float(variances[idx] / max_var)
        corr = _safe_abs_corr(x[:, idx], y) if y is not None else 0.0
        degree_cost = float(sum(alpha))
        score = normalized_variance + corr - memory_penalty * degree_cost
        if score > 0.75:
            status = "fertile"
        elif score > 0.1:
            status = "candidate"
        else:
            status = "m_minus_reject_candidate"
        out.append(
            FeatureFertility(
                alpha=alpha,
                score=float(score),
                variance=float(variances[idx]),
                target_correlation=float(corr),
                degree_cost=degree_cost,
                oak_status=status,
            )
        )
    return tuple(out)


def select_cvcd_features(
    lift: LiftResult,
    target: Sequence[float] | np.ndarray | None = None,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> CVCDSelection:
    """Select fertile features using simple CVCD score thresholds."""

    scores = feature_fertility_scores(lift, target)
    if not scores:
        return CVCDSelection(lift.features[:, []], tuple(), tuple(), tuple(), "empty")

    ranked = sorted(range(len(scores)), key=lambda i: scores[i].score, reverse=True)

    selected = []
    if top_k is not None:
        if top_k < 1:
            raise ValueError("top_k must be >= 1 when provided.")
        selected.extend(ranked[: min(top_k, len(ranked))])
    if min_score is not None:
        selected.extend(i for i, s in enumerate(scores) if s.score >= min_score)

    if top_k is None and min_score is None:
        selected.extend(ranked[: max(1, int(round(np.sqrt(len(ranked)))))] )

    zero_alpha = tuple(0 for _ in lift.alphas[0])
    for idx, alpha in enumerate(lift.alphas):
        if alpha == zero_alpha:
            selected.append(idx)
            break

    selected_tuple = tuple(sorted(set(int(i) for i in selected)))
    selected_features = lift.features[:, selected_tuple]
    selected_alphas = tuple(lift.alphas[i] for i in selected_tuple)

    status = "checked" if selected_tuple else "failed_empty_selection"
    return CVCDSelection(selected_features, selected_alphas, selected_tuple, scores, status)
