"""Bounded nonlinear experiment design using ensemble disagreement and risk gates."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ExperimentCandidate:
    experiment_id: str
    controls: tuple[float, ...]
    cost: float
    risk: float
    authorized: bool = True
    reversible: bool = True


@dataclass(frozen=True)
class DesignScore:
    experiment_id: str
    predictive_mean: float
    predictive_variance: float
    novelty_bonus: float
    utility: float
    accepted: bool
    reason: str


@dataclass(frozen=True)
class DesignReport:
    selected_experiment_id: str | None
    scores: tuple[DesignScore, ...]
    budget: float
    max_risk: float
    claim: str = "synthetic_expected_utility_only"


def _validate_candidate(candidate: ExperimentCandidate) -> None:
    if not candidate.experiment_id.strip():
        raise ValueError("experiment id cannot be blank")
    if not candidate.controls or not all(math.isfinite(value) for value in candidate.controls):
        raise ValueError("controls must be finite and non-empty")
    if not math.isfinite(candidate.cost) or candidate.cost < 0:
        raise ValueError("cost must be finite and non-negative")
    if not math.isfinite(candidate.risk) or not 0 <= candidate.risk <= 1:
        raise ValueError("risk must be within [0, 1]")


def ensemble_statistics(predictions: Sequence[float], weights: Sequence[float] | None = None) -> tuple[float, float]:
    if not predictions or not all(math.isfinite(value) for value in predictions):
        raise ValueError("predictions must be finite and non-empty")
    if weights is None:
        normalized = [1.0 / len(predictions)] * len(predictions)
    else:
        if len(weights) != len(predictions) or any(value < 0 or not math.isfinite(value) for value in weights):
            raise ValueError("invalid weights")
        total = sum(weights)
        if total <= 0:
            raise ValueError("weights must sum positive")
        normalized = [value / total for value in weights]
    mean = sum(weight * value for weight, value in zip(normalized, predictions, strict=True))
    variance = sum(weight * (value - mean) ** 2 for weight, value in zip(normalized, predictions, strict=True))
    return mean, variance


def score_experiments(
    candidates: Iterable[ExperimentCandidate],
    predictors: Sequence[Callable[[tuple[float, ...]], float]],
    *,
    model_weights: Sequence[float] | None = None,
    budget: float,
    max_risk: float,
    novelty: Mapping[str, float] | None = None,
    variance_weight: float = 1.0,
    novelty_weight: float = 0.25,
    cost_weight: float = 0.1,
    risk_weight: float = 1.0,
) -> DesignReport:
    if not predictors:
        raise ValueError("predictors cannot be empty")
    if not math.isfinite(budget) or budget < 0:
        raise ValueError("budget must be finite and non-negative")
    if not 0 <= max_risk <= 1:
        raise ValueError("max_risk must be within [0, 1]")
    seen: set[str] = set()
    scores: list[DesignScore] = []
    novelty = novelty or {}
    for candidate in candidates:
        _validate_candidate(candidate)
        if candidate.experiment_id in seen:
            raise ValueError("duplicate experiment id")
        seen.add(candidate.experiment_id)
        reason = "accepted"
        accepted = True
        if not candidate.authorized:
            accepted, reason = False, "unauthorized"
        elif not candidate.reversible:
            accepted, reason = False, "irreversible"
        elif candidate.cost > budget:
            accepted, reason = False, "over_budget"
        elif candidate.risk > max_risk:
            accepted, reason = False, "risk_exceeds_limit"
        predictions = [float(predictor(candidate.controls)) for predictor in predictors]
        if not all(math.isfinite(value) for value in predictions):
            raise ValueError("predictor returned non-finite value")
        mean, variance = ensemble_statistics(predictions, model_weights)
        bonus = float(novelty.get(candidate.experiment_id, 0.0))
        if not math.isfinite(bonus) or bonus < 0:
            raise ValueError("novelty bonus must be finite and non-negative")
        utility = variance_weight * variance + novelty_weight * bonus - cost_weight * candidate.cost - risk_weight * candidate.risk
        if not accepted:
            utility = -math.inf
        scores.append(
            DesignScore(
                experiment_id=candidate.experiment_id,
                predictive_mean=mean,
                predictive_variance=variance,
                novelty_bonus=bonus,
                utility=utility,
                accepted=accepted,
                reason=reason,
            )
        )
    ordered = tuple(sorted(scores, key=lambda item: (-item.utility, item.experiment_id)))
    selected = next((item.experiment_id for item in ordered if item.accepted), None)
    return DesignReport(selected_experiment_id=selected, scores=ordered, budget=budget, max_risk=max_risk)


def polynomial_predictor(coefficients: Sequence[float]) -> Callable[[tuple[float, ...]], float]:
    coeffs = tuple(float(value) for value in coefficients)
    if not coeffs or not all(math.isfinite(value) for value in coeffs):
        raise ValueError("coefficients must be finite and non-empty")

    def predict(controls: tuple[float, ...]) -> float:
        if len(controls) != 1:
            raise ValueError("polynomial predictor expects one control")
        x = controls[0]
        return sum(coefficient * x**power for power, coefficient in enumerate(coeffs))

    return predict
