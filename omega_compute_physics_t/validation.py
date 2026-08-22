"""R0.2 validation, model selection, uncertainty and drift for Ω-COMPUTE-PHYSICS-T∞.

This module stays dependency-free and deliberately separates:
- finite-domain empirical model selection;
- held-out predictive validation;
- split-conformal residual intervals;
- drift evidence;
from any mathematical asymptotic complexity proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import random
from statistics import median
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel, ResourceSample, fit_resource_model

_EPS = 1e-15


@dataclass(frozen=True)
class ModelCandidate:
    """Bounded empirical model-family candidate."""

    name: str
    max_total_degree: int = 1
    include_logs: bool = False
    include_xlogx: bool = False
    ridge: float = 1e-10
    max_features: int = 256


def default_candidates() -> tuple[ModelCandidate, ...]:
    """Conservative default family ordered from simple to richer."""

    return (
        ModelCandidate("linear", max_total_degree=1),
        ModelCandidate(
            "linear+log",
            max_total_degree=1,
            include_logs=True,
            include_xlogx=True,
        ),
        ModelCandidate("quadratic", max_total_degree=2),
        ModelCandidate(
            "quadratic+log",
            max_total_degree=2,
            include_logs=True,
            include_xlogx=True,
        ),
        ModelCandidate("cubic", max_total_degree=3),
    )


@dataclass(frozen=True)
class CandidateScore:
    name: str
    cv_rmse: float
    train_rmse: float
    active_parameters: int
    aic_proxy: float
    bic_proxy: float
    mdl_proxy: float
    valid: bool = True
    note: str = ""


@dataclass(frozen=True)
class ConformalInterval:
    """Symmetric split-conformal interval radius from held-out residuals.

    Under the usual exchangeability assumptions and with an untouched
    calibration split, this gives finite-sample marginal coverage for the
    fitted point predictor. It is not a guarantee under distribution shift.
    """

    alpha: float
    radius: float
    n_calibration: int
    empirical_calibration_coverage: float

    def bounds(self, prediction: float) -> tuple[float, float]:
        return prediction - self.radius, prediction + self.radius


@dataclass(frozen=True)
class ValidationReport:
    target: str
    selected_candidate: str
    selection_criterion: str
    n_total: int
    n_development: int
    n_calibration: int
    k_folds: int
    scores: tuple[CandidateScore, ...]
    calibration_rmse: float
    calibration_mae: float
    calibration_r2: float
    interval: ConformalInterval
    epistemic_level: str = "L2-held-out-validated-empirical"
    oak_warning: str = (
        "Held-out validation and conformal residual intervals characterize "
        "finite-domain empirical prediction only; they do not prove asymptotic "
        "Big-O/Theta complexity and do not guarantee coverage under drift."
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scores"] = [asdict(score) for score in self.scores]
        payload["interval"] = asdict(self.interval)
        return payload


@dataclass(frozen=True)
class ValidatedResourceModel:
    model: EmpiricalResourceModel
    report: ValidationReport

    def predict(self, point: Mapping[str, float]) -> float:
        return self.model.predict(point)

    def predict_interval(self, point: Mapping[str, float]) -> tuple[float, float, float]:
        value = self.predict(point)
        low, high = self.report.interval.bounds(value)
        return value, low, high

    def certificate(self) -> dict[str, Any]:
        return {
            "model": self.model.certificate(),
            "validation": self.report.to_dict(),
        }


@dataclass(frozen=True)
class DriftReport:
    target: str
    n_samples: int
    median_relative_error: float
    p95_relative_error: float
    exceedance_rate: float
    threshold: float
    trigger_fraction: float
    interval_miss_rate: float | None
    drift_detected: bool
    epistemic_level: str = "empirical-drift-sentinel"
    oak_warning: str = (
        "A drift flag is evidence that the empirical model no longer matches "
        "recent observations within the configured tolerance; it does not by "
        "itself identify the causal source of the change."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rmse(model: EmpiricalResourceModel, samples: Sequence[ResourceSample], target: str) -> float:
    if not samples:
        return math.nan
    errors = [
        float(sample.resources[target]) - model.predict(sample.variables)
        for sample in samples
    ]
    return math.sqrt(sum(error * error for error in errors) / len(errors))


def _mae(model: EmpiricalResourceModel, samples: Sequence[ResourceSample], target: str) -> float:
    if not samples:
        return math.nan
    return sum(
        abs(float(sample.resources[target]) - model.predict(sample.variables))
        for sample in samples
    ) / len(samples)


def _r2(model: EmpiricalResourceModel, samples: Sequence[ResourceSample], target: str) -> float:
    if not samples:
        return math.nan
    observed = [float(sample.resources[target]) for sample in samples]
    predicted = [model.predict(sample.variables) for sample in samples]
    mean_y = sum(observed) / len(observed)
    ss_res = sum((y - yhat) ** 2 for y, yhat in zip(observed, predicted))
    ss_tot = sum((y - mean_y) ** 2 for y in observed)
    if ss_tot <= _EPS:
        return 1.0 if ss_res <= _EPS else 0.0
    return 1.0 - ss_res / ss_tot


def _fit_candidate(
    samples: Sequence[ResourceSample],
    target: str,
    candidate: ModelCandidate,
) -> EmpiricalResourceModel:
    return fit_resource_model(
        samples,
        target,
        max_total_degree=candidate.max_total_degree,
        include_logs=candidate.include_logs,
        include_xlogx=candidate.include_xlogx,
        ridge=candidate.ridge,
        max_features=candidate.max_features,
    )


def _active_parameters(model: EmpiricalResourceModel, threshold: float = 1e-10) -> int:
    return max(1, sum(abs(value) > threshold for value in model.coefficients))


def _information_proxies(
    model: EmpiricalResourceModel,
    samples: Sequence[ResourceSample],
    target: str,
) -> tuple[float, float, float]:
    """Gaussian-residual AIC/BIC/MDL-style proxies.

    For ridge fits these are model-comparison heuristics rather than exact
    likelihood-theory information criteria, hence the explicit ``_proxy`` names.
    """

    n = len(samples)
    residuals = [
        float(sample.resources[target]) - model.predict(sample.variables)
        for sample in samples
    ]
    sse = sum(value * value for value in residuals)
    sigma2 = max(sse / max(n, 1), _EPS)
    k = _active_parameters(model)
    base = n * math.log(sigma2)
    aic = base + 2.0 * k
    bic = base + math.log(max(n, 2)) * k
    mdl = 0.5 * (
        n * math.log(2.0 * math.pi * sigma2)
        + n
        + k * math.log(max(n, 2))
    )
    return aic, bic, mdl


def _deterministic_shuffle(
    samples: Sequence[ResourceSample],
    *,
    seed: int,
) -> list[ResourceSample]:
    ordered = sorted(
        samples,
        key=lambda sample: json.dumps(
            {
                "variables": dict(sorted(sample.variables.items())),
                "resources": dict(sorted(sample.resources.items())),
                "metadata": dict(sorted((str(k), str(v)) for k, v in sample.metadata.items())),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    rng = random.Random(seed)
    rng.shuffle(ordered)
    return ordered


def development_calibration_split(
    samples: Sequence[ResourceSample],
    *,
    calibration_fraction: float = 0.2,
    seed: int = 0,
) -> tuple[list[ResourceSample], list[ResourceSample]]:
    """Make a deterministic development/calibration split."""

    if len(samples) < 8:
        raise ValueError("R0.2 validated fitting requires at least 8 samples")
    if not 0.1 <= calibration_fraction <= 0.4:
        raise ValueError("calibration_fraction must be in [0.1, 0.4]")
    shuffled = _deterministic_shuffle(samples, seed=seed)
    n_calibration = max(2, int(round(len(shuffled) * calibration_fraction)))
    n_calibration = min(n_calibration, len(shuffled) - 4)
    calibration = shuffled[:n_calibration]
    development = shuffled[n_calibration:]
    return development, calibration


def cross_validated_rmse(
    samples: Sequence[ResourceSample],
    target: str,
    candidate: ModelCandidate,
    *,
    k_folds: int = 5,
    seed: int = 0,
) -> float:
    """Deterministic K-fold predictive RMSE over development samples."""

    if len(samples) < 4:
        raise ValueError("cross validation needs at least four samples")
    k = max(2, min(k_folds, len(samples) // 2))
    shuffled = _deterministic_shuffle(samples, seed=seed)
    squared_errors: list[float] = []
    for fold in range(k):
        validation = [sample for index, sample in enumerate(shuffled) if index % k == fold]
        training = [sample for index, sample in enumerate(shuffled) if index % k != fold]
        if len(training) < 2 or not validation:
            continue
        model = _fit_candidate(training, target, candidate)
        for sample in validation:
            error = float(sample.resources[target]) - model.predict(sample.variables)
            squared_errors.append(error * error)
    if not squared_errors:
        raise ValueError("cross validation produced no held-out predictions")
    return math.sqrt(sum(squared_errors) / len(squared_errors))


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot take a quantile of an empty sequence")
    ordered = sorted(float(value) for value in values)
    probability = min(max(probability, 0.0), 1.0)
    index = int(math.ceil(probability * len(ordered))) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def _conformal_interval(
    model: EmpiricalResourceModel,
    calibration: Sequence[ResourceSample],
    target: str,
    *,
    alpha: float,
) -> ConformalInterval:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    residuals = [
        abs(float(sample.resources[target]) - model.predict(sample.variables))
        for sample in calibration
    ]
    n = len(residuals)
    rank_probability = min(1.0, math.ceil((n + 1) * (1.0 - alpha)) / n)
    radius = _quantile(residuals, rank_probability)
    coverage = sum(value <= radius + _EPS for value in residuals) / n
    return ConformalInterval(
        alpha=alpha,
        radius=radius,
        n_calibration=n,
        empirical_calibration_coverage=coverage,
    )


def fit_validated_resource_model(
    samples: Sequence[ResourceSample],
    target: str,
    *,
    candidates: Sequence[ModelCandidate] | None = None,
    selection_criterion: str = "cv_rmse",
    calibration_fraction: float = 0.2,
    alpha: float = 0.1,
    k_folds: int = 5,
    seed: int = 0,
) -> ValidatedResourceModel:
    """Select a compact empirical law, validate it, and calibrate uncertainty.

    Model selection uses only the development partition. The calibration
    partition stays untouched until after selection so its residuals can serve
    as split-conformal calibration evidence.
    """

    if candidates is None:
        candidates = default_candidates()
    if not candidates:
        raise ValueError("at least one model candidate is required")
    allowed = {"cv_rmse", "aic_proxy", "bic_proxy", "mdl_proxy"}
    if selection_criterion not in allowed:
        raise ValueError(f"selection_criterion must be one of {sorted(allowed)}")

    development, calibration = development_calibration_split(
        samples,
        calibration_fraction=calibration_fraction,
        seed=seed,
    )

    rows: list[tuple[CandidateScore, EmpiricalResourceModel]] = []
    failures: list[CandidateScore] = []
    for candidate in candidates:
        try:
            cv = cross_validated_rmse(
                development,
                target,
                candidate,
                k_folds=k_folds,
                seed=seed + 17,
            )
            model = _fit_candidate(development, target, candidate)
            aic, bic, mdl = _information_proxies(model, development, target)
            score = CandidateScore(
                name=candidate.name,
                cv_rmse=cv,
                train_rmse=_rmse(model, development, target),
                active_parameters=_active_parameters(model),
                aic_proxy=aic,
                bic_proxy=bic,
                mdl_proxy=mdl,
            )
            rows.append((score, model))
        except (ValueError, KeyError, OverflowError, ZeroDivisionError) as exc:
            failures.append(
                CandidateScore(
                    name=candidate.name,
                    cv_rmse=math.inf,
                    train_rmse=math.inf,
                    active_parameters=0,
                    aic_proxy=math.inf,
                    bic_proxy=math.inf,
                    mdl_proxy=math.inf,
                    valid=False,
                    note=f"{type(exc).__name__}: {exc}",
                )
            )

    if not rows:
        notes = "; ".join(f"{row.name}: {row.note}" for row in failures)
        raise ValueError(f"all empirical model candidates failed: {notes}")

    def criterion(item: tuple[CandidateScore, EmpiricalResourceModel]) -> tuple[float, int, str]:
        score, _ = item
        value = float(getattr(score, selection_criterion))
        return value, score.active_parameters, score.name

    selected_score, selected_model = min(rows, key=criterion)
    interval = _conformal_interval(
        selected_model,
        calibration,
        target,
        alpha=alpha,
    )

    report = ValidationReport(
        target=target,
        selected_candidate=selected_score.name,
        selection_criterion=selection_criterion,
        n_total=len(samples),
        n_development=len(development),
        n_calibration=len(calibration),
        k_folds=max(2, min(k_folds, len(development) // 2)),
        scores=tuple(score for score, _ in rows) + tuple(failures),
        calibration_rmse=_rmse(selected_model, calibration, target),
        calibration_mae=_mae(selected_model, calibration, target),
        calibration_r2=_r2(selected_model, calibration, target),
        interval=interval,
    )
    return ValidatedResourceModel(selected_model, report)


def detect_drift(
    model: EmpiricalResourceModel,
    samples: Sequence[ResourceSample],
    target: str,
    *,
    relative_error_threshold: float = 0.20,
    trigger_fraction: float = 0.30,
    interval: ConformalInterval | None = None,
) -> DriftReport:
    """Flag persistent predictive mismatch without inventing a causal story."""

    if not samples:
        raise ValueError("drift detection requires samples")
    if relative_error_threshold <= 0:
        raise ValueError("relative_error_threshold must be positive")
    if not 0.0 <= trigger_fraction <= 1.0:
        raise ValueError("trigger_fraction must be in [0, 1]")

    relative_errors: list[float] = []
    misses = 0
    for sample in samples:
        actual = float(sample.resources[target])
        predicted = model.predict(sample.variables)
        denominator = max(abs(actual), abs(predicted), _EPS)
        relative_errors.append(abs(actual - predicted) / denominator)
        if interval is not None:
            low, high = interval.bounds(predicted)
            misses += not (low <= actual <= high)

    exceedance_rate = sum(
        value > relative_error_threshold for value in relative_errors
    ) / len(relative_errors)
    interval_miss_rate = None if interval is None else misses / len(samples)
    drift = exceedance_rate >= trigger_fraction
    if interval_miss_rate is not None:
        drift = drift or interval_miss_rate > min(1.0, 2.0 * interval.alpha + 0.05)

    return DriftReport(
        target=target,
        n_samples=len(samples),
        median_relative_error=median(relative_errors),
        p95_relative_error=_quantile(relative_errors, 0.95),
        exceedance_rate=exceedance_rate,
        threshold=relative_error_threshold,
        trigger_fraction=trigger_fraction,
        interval_miss_rate=interval_miss_rate,
        drift_detected=drift,
    )
