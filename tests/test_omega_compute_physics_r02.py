"""Focused R0.2 tests for validation, uncertainty, drift and Complexity Diff."""

from __future__ import annotations

import math

from omega_compute_physics_t.atlas import ResourceSample, fit_resource_model
from omega_compute_physics_t.complexity_diff import (
    compare_models,
    geometric_sweep,
    model_from_serialized,
)
from omega_compute_physics_t.validation import (
    ModelCandidate,
    detect_drift,
    fit_validated_resource_model,
)


def _sample(n: float, value: float) -> ResourceSample:
    return ResourceSample(
        variables={"n": float(n)},
        resources={"wall_time_s": float(value)},
        metadata={"campaign": "r02-test"},
    )


def test_validated_fit_holds_out_calibration_and_builds_interval() -> None:
    samples = []
    for n in range(1, 61):
        noise = ((n % 7) - 3) * 0.004
        samples.append(_sample(n, 1.25 + 0.4 * n + noise))

    validated = fit_validated_resource_model(
        samples,
        "wall_time_s",
        candidates=(
            ModelCandidate("linear", max_total_degree=1),
            ModelCandidate("quadratic", max_total_degree=2),
        ),
        calibration_fraction=0.2,
        alpha=0.1,
        k_folds=5,
        seed=11,
    )

    assert validated.report.n_total == 60
    assert validated.report.n_calibration >= 2
    assert validated.report.n_development + validated.report.n_calibration == 60
    assert validated.report.calibration_rmse < 0.05
    assert validated.report.interval.radius >= 0.0
    prediction, low, high = validated.predict_interval({"n": 30.0})
    assert low <= prediction <= high
    assert validated.report.epistemic_level.startswith("L2-")


def test_selection_returns_a_predictively_valid_candidate() -> None:
    samples = [_sample(n, 3.0 + 2.0 * n) for n in range(1, 51)]
    validated = fit_validated_resource_model(
        samples,
        "wall_time_s",
        candidates=(
            ModelCandidate("linear", max_total_degree=1),
            ModelCandidate("cubic", max_total_degree=3),
        ),
        selection_criterion="cv_rmse",
        seed=3,
    )
    assert validated.report.selected_candidate in {"linear", "cubic"}
    assert validated.report.calibration_rmse < 1e-5


def test_drift_sentinel_flags_persistent_shift() -> None:
    baseline = [_sample(n, 2.0 + 0.25 * n) for n in range(1, 41)]
    validated = fit_validated_resource_model(
        baseline,
        "wall_time_s",
        candidates=(ModelCandidate("linear", max_total_degree=1),),
        seed=5,
    )
    shifted = [_sample(n, 1.7 * (2.0 + 0.25 * n)) for n in range(10, 30)]
    report = detect_drift(
        validated.model,
        shifted,
        "wall_time_s",
        relative_error_threshold=0.15,
        trigger_fraction=0.5,
        interval=validated.report.interval,
    )
    assert report.drift_detected
    assert report.exceedance_rate >= 0.5
    assert report.median_relative_error > 0.15


def test_complexity_diff_detects_uniform_improvement_and_preserved_exponent() -> None:
    old_samples = [_sample(n, n * n) for n in range(1, 31)]
    new_samples = [_sample(n, 0.8 * n * n) for n in range(1, 31)]
    old = fit_resource_model(
        old_samples,
        "wall_time_s",
        max_total_degree=2,
        include_logs=False,
        include_xlogx=False,
    )
    new = fit_resource_model(
        new_samples,
        "wall_time_s",
        max_total_degree=2,
        include_logs=False,
        include_xlogx=False,
    )
    points = geometric_sweep("n", 2.0, 30.0, count=20)
    report = compare_models(
        old,
        new,
        points,
        direction="lower-is-better",
        relative_tolerance=0.01,
        elasticity_anchor={"n": 10.0},
    )

    assert report.improvement_fraction == 1.0
    assert report.regression_fraction == 0.0
    assert -0.21 < report.mean_relative_change < -0.19
    assert report.elasticity_delta is not None
    assert abs(report.elasticity_delta["n"]) < 1e-3


def test_complexity_diff_finds_sampled_crossover_candidate() -> None:
    old_samples = [_sample(n, n) for n in range(1, 41)]
    new_samples = [_sample(n, 0.5 * n + 0.02 * n * n) for n in range(1, 41)]
    old = fit_resource_model(
        old_samples,
        "wall_time_s",
        max_total_degree=2,
        include_logs=False,
        include_xlogx=False,
    )
    new = fit_resource_model(
        new_samples,
        "wall_time_s",
        max_total_degree=2,
        include_logs=False,
        include_xlogx=False,
    )
    points = [{"n": float(n)} for n in range(5, 36)]
    report = compare_models(old, new, points)
    assert report.crossover_candidates
    crossover = report.crossover_candidates[0]["n"]
    assert 24.0 <= crossover <= 26.0


def test_serialized_model_roundtrip_prediction() -> None:
    model = fit_resource_model(
        [_sample(n, 2.0 + 3.0 * n) for n in range(1, 20)],
        "wall_time_s",
        max_total_degree=1,
        include_logs=False,
        include_xlogx=False,
    )
    payload = {
        **model.certificate(),
        "features": [
            {
                "kind": feature.kind,
                "variables": list(feature.variables),
                "powers": list(feature.powers),
                "label": feature.label,
            }
            for feature in model.features
        ],
        "coefficients": list(model.coefficients),
    }
    restored = model_from_serialized(payload)
    assert math.isclose(
        restored.predict({"n": 12.0}),
        model.predict({"n": 12.0}),
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
