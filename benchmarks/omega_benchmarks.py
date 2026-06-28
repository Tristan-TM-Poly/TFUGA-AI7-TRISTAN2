"""Small reproducible benchmarks for Ω-VTP-T++.

Run with:
    python benchmarks/omega_benchmarks.py

The goal is not to beat optimized scientific libraries yet. The goal is to keep
residual/time/feature-count measurements visible as the framework evolves.
"""

from __future__ import annotations

from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from omega_vtp_t import (
    PolynomialODE,
    build_carleman_operator,
    carleman_residual_on_samples,
    fit_koopman_tensorprod,
    tensor_prod_lift,
)


def benchmark_logistic_carleman() -> dict[str, float | int | str]:
    ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): -0.2},))
    samples = np.linspace(-0.5, 0.5, 512).reshape(-1, 1)
    start = time.perf_counter()
    report = carleman_residual_on_samples(ode, samples, degree=4)
    elapsed = time.perf_counter() - start
    return {
        "benchmark": "logistic_carleman_degree4",
        "elapsed_seconds": elapsed,
        "feature_count": int(report["feature_count"]),
        "sample_relative_residual": float(report["sample_relative_residual"]),
        "oak_status": str(report["oak_status"]),
    }


def benchmark_koopman_polynomial_map() -> dict[str, float | int | str]:
    x = np.linspace(-1, 1, 512).reshape(-1, 1)
    y = 0.5 * x + 0.1 * x**2
    start = time.perf_counter()
    fit = fit_koopman_tensorprod(x, y, degree=3, lift="monomial")
    elapsed = time.perf_counter() - start
    return {
        "benchmark": "koopman_polynomial_map_degree3",
        "elapsed_seconds": elapsed,
        "feature_count": int(fit.fit.report.feature_count),
        "relative_residual": float(fit.fit.report.relative_residual),
        "closure_coefficient": float(fit.closure.closure_coefficient),
        "oak_status": fit.fit.report.oak_status,
    }


def benchmark_lift_feature_count() -> dict[str, float | int | str]:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(1024, 4))
    start = time.perf_counter()
    lift = tensor_prod_lift(x, degree=3)
    elapsed = time.perf_counter() - start
    return {
        "benchmark": "tensor_prod_lift_1024x4_degree3",
        "elapsed_seconds": elapsed,
        "feature_count": lift.features.shape[1],
        "sample_count": lift.features.shape[0],
        "oak_status": "measured",
    }


def run_all() -> list[dict[str, float | int | str]]:
    return [
        benchmark_logistic_carleman(),
        benchmark_koopman_polynomial_map(),
        benchmark_lift_feature_count(),
    ]


if __name__ == "__main__":
    for item in run_all():
        print(item)
