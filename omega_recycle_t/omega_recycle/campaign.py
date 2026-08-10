from __future__ import annotations

from dataclasses import dataclass, field
import math


@dataclass(frozen=True, slots=True)
class PredictionCase:
    case_id: str
    observed_value: float
    predictions: dict[str, float] = field(default_factory=dict)
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.case_id or not self.predictions:
            raise ValueError("case_id and predictions are required")
        if self.weight <= 0:
            raise ValueError("weight must be positive")
        if not all(math.isfinite(value) for value in (self.observed_value, *self.predictions.values())):
            raise ValueError("values must be finite")


@dataclass(frozen=True, slots=True)
class MethodMetrics:
    method: str
    mae: float
    rmse: float
    bias: float


@dataclass(frozen=True, slots=True)
class PredictionCampaignReport:
    metrics: tuple[MethodMetrics, ...]
    best_method_by_rmse: str
    canonical_method: str
    canonical_rmse_regret: float
    canonical_is_best: bool
    claim_boundary: str = "prediction_campaign_only_no_causal_or_industrial_superiority_claim"


def evaluate_prediction_campaign(
    cases: tuple[PredictionCase, ...],
    *,
    canonical_method: str,
) -> PredictionCampaignReport:
    if not cases:
        raise ValueError("at least one case is required")
    methods = set(cases[0].predictions)
    if canonical_method not in methods:
        raise ValueError("canonical_method missing")
    for case in cases:
        if set(case.predictions) != methods:
            raise ValueError("all cases must expose identical methods")
    total_weight = sum(case.weight for case in cases)
    metrics: list[MethodMetrics] = []
    for method in sorted(methods):
        errors = [(case.predictions[method] - case.observed_value, case.weight) for case in cases]
        mae = sum(weight * abs(error) for error, weight in errors) / total_weight
        mse = sum(weight * error * error for error, weight in errors) / total_weight
        bias = sum(weight * error for error, weight in errors) / total_weight
        metrics.append(MethodMetrics(method, mae, math.sqrt(mse), bias))
    best = min(metrics, key=lambda item: (item.rmse, item.mae, abs(item.bias), item.method))
    canonical = next(item for item in metrics if item.method == canonical_method)
    regret = canonical.rmse - best.rmse
    return PredictionCampaignReport(
        metrics=tuple(metrics),
        best_method_by_rmse=best.method,
        canonical_method=canonical_method,
        canonical_rmse_regret=regret,
        canonical_is_best=abs(regret) <= 1e-12,
    )
