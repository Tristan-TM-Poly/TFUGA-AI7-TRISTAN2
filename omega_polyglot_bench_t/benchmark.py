"""Deterministic conformance benchmarks and backend selection."""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Iterable, Sequence
from time import perf_counter_ns

from .contracts import BackendMeasurement, BenchmarkReport
from .native import NativeVectorAffine
from .reference import vector_affine_python

BackendCallable = Callable[[Sequence[float], Sequence[float], float], list[float]]
SUPPORTED_BACKENDS = ("python", "c", "cpp", "rust")


def generate_vectors(size: int, seed: int) -> tuple[list[float], list[float]]:
    if size < 0:
        raise ValueError("size must be non-negative")
    generator = random.Random(seed)
    return (
        [generator.uniform(-1.0, 1.0) for _ in range(size)],
        [generator.uniform(-1.0, 1.0) for _ in range(size)],
    )


def _backend_callable(name: str) -> BackendCallable:
    if name == "python":
        return vector_affine_python
    if name in {"c", "cpp", "rust"}:
        return NativeVectorAffine(name)
    raise ValueError(f"unknown backend: {name}")


def _percentile_95(samples: list[int]) -> int:
    ordered = sorted(samples)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index]


def _measure_backend(
    name: str,
    x: Sequence[float],
    y: Sequence[float],
    scalar: float,
    expected: Sequence[float],
    warmups: int,
    repetitions: int,
    tolerance: float,
) -> BackendMeasurement:
    try:
        implementation = _backend_callable(name)
    except (FileNotFoundError, OSError, RuntimeError) as error:
        return BackendMeasurement(
            backend=name,
            available=False,
            correct=False,
            cold_ns=None,
            median_ns=None,
            p95_ns=None,
            mean_ns=None,
            max_abs_error=None,
            repetitions=0,
            notes=(str(error),),
        )

    cold_start = perf_counter_ns()
    actual = implementation(x, y, scalar)
    cold_ns = perf_counter_ns() - cold_start
    if len(actual) != len(expected):
        return BackendMeasurement(
            backend=name,
            available=True,
            correct=False,
            cold_ns=cold_ns,
            median_ns=None,
            p95_ns=None,
            mean_ns=None,
            max_abs_error=None,
            repetitions=0,
            notes=("output length differs from the Python oracle",),
        )

    max_abs_error = max(
        (abs(float(observed) - float(reference)) for observed, reference in zip(actual, expected, strict=True)),
        default=0.0,
    )
    correct = math.isfinite(max_abs_error) and max_abs_error <= tolerance
    if not correct:
        return BackendMeasurement(
            backend=name,
            available=True,
            correct=False,
            cold_ns=cold_ns,
            median_ns=None,
            p95_ns=None,
            mean_ns=None,
            max_abs_error=max_abs_error,
            repetitions=0,
            notes=(f"conformance failed at tolerance {tolerance}",),
        )

    for _ in range(warmups):
        implementation(x, y, scalar)

    samples: list[int] = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        implementation(x, y, scalar)
        samples.append(perf_counter_ns() - start)

    return BackendMeasurement(
        backend=name,
        available=True,
        correct=True,
        cold_ns=cold_ns,
        median_ns=int(statistics.median(samples)),
        p95_ns=_percentile_95(samples),
        mean_ns=statistics.fmean(samples),
        max_abs_error=max_abs_error,
        repetitions=repetitions,
        notes=("timing includes Python-to-native conversion and output materialization",)
        if name != "python"
        else ("plain Python behavioral oracle",),
    )


def select_backend(measurements: Iterable[BackendMeasurement]) -> str | None:
    eligible = [
        item
        for item in measurements
        if item.available and item.correct and item.median_ns is not None
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda item: (item.median_ns, item.backend)).backend


def benchmark_backends(
    *,
    size: int = 100_000,
    scalar: float = 1.75,
    seed: int = 1729,
    warmups: int = 3,
    repetitions: int = 15,
    tolerance: float = 1e-12,
    backends: Iterable[str] = SUPPORTED_BACKENDS,
) -> BenchmarkReport:
    if warmups < 0:
        raise ValueError("warmups must be non-negative")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")

    requested = tuple(dict.fromkeys(backends))
    unknown = sorted(set(requested) - set(SUPPORTED_BACKENDS))
    if unknown:
        raise ValueError(f"unknown backends: {', '.join(unknown)}")

    x, y = generate_vectors(size, seed)
    expected = vector_affine_python(x, y, scalar)
    measurements = tuple(
        _measure_backend(
            backend,
            x,
            y,
            scalar,
            expected,
            warmups,
            repetitions,
            tolerance,
        )
        for backend in requested
    )
    return BenchmarkReport(
        algorithm="vector_affine_f64",
        size=size,
        scalar=scalar,
        seed=seed,
        warmups=warmups,
        repetitions=repetitions,
        includes_ffi_conversion=True,
        measurements=measurements,
        selected_backend=select_backend(measurements),
    )
