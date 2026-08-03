"""Size-aware differential autotuner for native, NumPy and Python baselines."""
from __future__ import annotations

import json
import math
import os
import platform
import random
import statistics
from array import array
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable, Iterable

from .buffers import double_array, zeros
from .build import BACKENDS, PROFILES, default_build_dir
from .contracts import AutotuneReport, CandidateMeasurement, SizeChampion
from .native import AFFINE_VARIANTS, CHAIN_VARIANTS, REDUCTION_VARIANTS, KernelLibrary


def hardware_fingerprint() -> dict[str, Any]:
    payload = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
    }
    try:
        import numpy as np
        payload["numpy"] = np.__version__
    except ImportError:
        payload["numpy"] = None
    return payload


def generate_vectors(size: int, seed: int) -> tuple[array, array, array]:
    rng = random.Random(seed)
    x = double_array(rng.uniform(-1.0, 1.0) for _ in range(size))
    y = double_array(rng.uniform(-1.0, 1.0) for _ in range(size))
    z = double_array(rng.uniform(-1.0, 1.0) for _ in range(size))
    return x, y, z


def python_affine(x: array, y: array, scalar: float) -> list[float]:
    return [scalar * a + b for a, b in zip(x, y, strict=True)]


def python_chain(x: array, y: array, z: array, a: float, b: float) -> list[float]:
    return [b * (a * xv + yv) + zv for xv, yv, zv in zip(x, y, z, strict=True)]


def python_sum(x: array) -> float:
    return sum(x)


def python_dot(x: array, y: array) -> float:
    return sum(a * b for a, b in zip(x, y, strict=True))


def _p95(samples: list[int]) -> int:
    return sorted(samples)[max(0, math.ceil(0.95 * len(samples)) - 1)]


def _timed(fn: Callable[[], Any], warmups: int, repetitions: int) -> tuple[int, float, int]:
    for _ in range(warmups):
        fn()
    samples: list[int] = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        fn()
        samples.append(perf_counter_ns() - start)
    return int(statistics.median(samples)), statistics.fmean(samples), _p95(samples)


def _max_error(actual: Iterable[float], expected: Iterable[float]) -> float:
    return max((abs(float(a) - float(b)) for a, b in zip(actual, expected, strict=True)), default=0.0)


def discover_libraries(
    backends: Iterable[str] = BACKENDS,
    profiles: Iterable[str] = PROFILES,
    build_dir: Path | None = None,
) -> list[KernelLibrary]:
    libraries: list[KernelLibrary] = []
    for backend in backends:
        for profile in profiles:
            try:
                libraries.append(KernelLibrary(backend, profile, build_dir or default_build_dir()))
            except (FileNotFoundError, OSError):
                continue
    return libraries


def _candidate(
    algorithm: str,
    backend: str,
    profile: str,
    variant: str,
    size: int,
    correct: bool,
    timing: tuple[int, float, int] | None,
    setup_ns: int,
    error: float,
    python_median: int,
    bytes_per_element: float,
    features: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> CandidateMeasurement:
    median, mean, p95 = timing if timing is not None else (None, None, None)
    return CandidateMeasurement(
        algorithm, backend, profile, variant, size, correct,
        median, mean, p95, setup_ns, error,
        python_median / median if correct and median else None,
        (bytes_per_element * size) / median if correct and median else None,
        features, notes,
    )


def _measure_affine(
    lib: KernelLibrary, variant: str, x: array, y: array, scalar: float,
    expected: list[float], python_median: int, warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement:
    start = perf_counter_ns()
    prepared = lib.prepare_affine(variant, x, y, zeros(len(x)))
    setup_ns = perf_counter_ns() - start
    actual = prepared.run(scalar)
    error = _max_error(actual, expected)
    correct = math.isfinite(error) and error <= tolerance
    timing = _timed(lambda: prepared.run(scalar), warmups, repetitions) if correct else None
    return _candidate("affine", lib.backend, lib.profile, variant, len(x), correct, timing, setup_ns, error, python_median, 24.0, lib.features, () if correct else ("conformance_failed",))


def _measure_numpy_affine(
    x: array, y: array, scalar: float, expected: list[float], python_median: int,
    warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement | None:
    try:
        import numpy as np
    except ImportError:
        return None
    start = perf_counter_ns()
    xv = np.frombuffer(x, dtype=np.float64)
    yv = np.frombuffer(y, dtype=np.float64)
    out = np.empty_like(xv)
    setup_ns = perf_counter_ns() - start
    def run() -> Any:
        np.multiply(xv, scalar, out=out)
        np.add(out, yv, out=out)
        return out
    actual = run()
    error = _max_error(actual, expected)
    correct = math.isfinite(error) and error <= tolerance
    timing = _timed(run, warmups, repetitions) if correct else None
    return _candidate("affine", "python", "numpy", "ufunc_out", len(x), correct, timing, setup_ns, error, python_median, 24.0, (), ("zero_copy_input_views",))


def _measure_chain_fused(
    lib: KernelLibrary, variant: str, x: array, y: array, z: array, a: float, b: float,
    expected: list[float], python_median: int, warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement:
    start = perf_counter_ns()
    prepared = lib.prepare_chain(x, y, z, zeros(len(x)), variant=variant)
    setup_ns = perf_counter_ns() - start
    actual = prepared.run(a, b)
    error = _max_error(actual, expected)
    correct = math.isfinite(error) and error <= tolerance
    timing = _timed(lambda: prepared.run(a, b), warmups, repetitions) if correct else None
    return _candidate("affine_chain", lib.backend, lib.profile, f"fused_{variant}", len(x), correct, timing, setup_ns, error, python_median, 32.0, lib.features, ("single_native_pass",))


def _measure_chain_two_pass(
    lib: KernelLibrary, variant: str, x: array, y: array, z: array, a: float, b: float,
    expected: list[float], python_median: int, warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement:
    start = perf_counter_ns()
    temp = zeros(len(x))
    out = zeros(len(x))
    first = lib.prepare_affine(variant, x, y, temp)
    second = lib.prepare_affine(variant, temp, z, out)
    setup_ns = perf_counter_ns() - start
    def run() -> Any:
        first.run(a)
        return second.run(b)
    actual = run()
    error = _max_error(actual, expected)
    correct = math.isfinite(error) and error <= tolerance
    timing = _timed(run, warmups, repetitions) if correct else None
    return _candidate("affine_chain", lib.backend, lib.profile, f"two_pass_{variant}", len(x), correct, timing, setup_ns, error, python_median, 48.0, lib.features, ("two_native_passes",))


def _measure_numpy_chain(
    x: array, y: array, z: array, a: float, b: float, expected: list[float],
    python_median: int, warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement | None:
    try:
        import numpy as np
    except ImportError:
        return None
    start = perf_counter_ns()
    xv = np.frombuffer(x, dtype=np.float64)
    yv = np.frombuffer(y, dtype=np.float64)
    zv = np.frombuffer(z, dtype=np.float64)
    temp = np.empty_like(xv)
    out = np.empty_like(xv)
    setup_ns = perf_counter_ns() - start
    def run() -> Any:
        np.multiply(xv, a, out=temp)
        np.add(temp, yv, out=temp)
        np.multiply(temp, b, out=out)
        np.add(out, zv, out=out)
        return out
    actual = run()
    error = _max_error(actual, expected)
    correct = math.isfinite(error) and error <= tolerance
    timing = _timed(run, warmups, repetitions) if correct else None
    return _candidate("affine_chain", "python", "numpy", "four_ufunc_passes", len(x), correct, timing, setup_ns, error, python_median, 64.0, (), ("zero_copy_input_views", "temporary_buffer"))


def _measure_reduction(
    lib: KernelLibrary, operation: str, variant: str, x: array, y: array, expected: float,
    python_median: int, warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement:
    start = perf_counter_ns()
    prepared = lib.prepare_reduction(operation, x, y if operation == "dot" else None, variant=variant)
    setup_ns = perf_counter_ns() - start
    actual = prepared.run()
    error = abs(actual - expected)
    scaled_tolerance = tolerance * max(1.0, abs(expected), len(x))
    correct = math.isfinite(error) and error <= scaled_tolerance
    timing = _timed(prepared.run, warmups, repetitions) if correct else None
    return _candidate(operation, lib.backend, lib.profile, f"{variant}_reduction", len(x), correct, timing, setup_ns, error, python_median, 16.0 if operation == "dot" else 8.0, lib.features, () if correct else ("conformance_failed",))


def _measure_numpy_reduction(
    operation: str, x: array, y: array, expected: float, python_median: int,
    warmups: int, repetitions: int, tolerance: float,
) -> CandidateMeasurement | None:
    try:
        import numpy as np
    except ImportError:
        return None
    start = perf_counter_ns()
    xv = np.frombuffer(x, dtype=np.float64)
    yv = np.frombuffer(y, dtype=np.float64)
    setup_ns = perf_counter_ns() - start
    fn = (lambda: float(np.sum(xv))) if operation == "sum" else (lambda: float(np.dot(xv, yv)))
    actual = fn()
    error = abs(actual - expected)
    scaled_tolerance = tolerance * max(1.0, abs(expected), len(x))
    correct = math.isfinite(error) and error <= scaled_tolerance
    timing = _timed(fn, warmups, repetitions) if correct else None
    return _candidate(operation, "python", "numpy", operation, len(x), correct, timing, setup_ns, error, python_median, 16.0 if operation == "dot" else 8.0, (), ("zero_copy_input_views",))


def _select_champion(algorithm: str, size: int, group: list[CandidateMeasurement]) -> SizeChampion | None:
    eligible = [m for m in group if m.correct and m.median_ns is not None]
    if not eligible:
        return None
    winner = min(eligible, key=lambda m: (m.median_ns, m.candidate_id))
    return SizeChampion(algorithm, size, winner.candidate_id, winner.median_ns or 0, winner.speedup_vs_python, winner.max_abs_error or 0.0)


def autotune(
    *,
    sizes: tuple[int, ...] = (16, 256, 4096, 100_000, 1_000_000),
    backends: tuple[str, ...] = BACKENDS,
    profiles: tuple[str, ...] = PROFILES,
    algorithms: tuple[str, ...] = ("affine", "affine_chain", "sum", "dot"),
    warmups: int = 3,
    repetitions: int = 15,
    tolerance: float = 1e-12,
    seed: int = 1729,
    scalar: float = 1.75,
    chain_b: float = -0.625,
    build_dir: Path | None = None,
) -> AutotuneReport:
    if any(size < 0 for size in sizes):
        raise ValueError("sizes must be non-negative")
    if repetitions <= 0 or warmups < 0:
        raise ValueError("invalid warmups/repetitions")
    libraries = discover_libraries(backends, profiles, build_dir)
    measurements: list[CandidateMeasurement] = []
    champions: list[SizeChampion] = []

    for size in sizes:
        x, y, z = generate_vectors(size, seed + size)
        if "affine" in algorithms:
            expected = python_affine(x, y, scalar)
            py_median, _, _ = _timed(lambda: python_affine(x, y, scalar), warmups, repetitions)
            group: list[CandidateMeasurement] = []
            np_item = _measure_numpy_affine(x, y, scalar, expected, py_median, warmups, repetitions, tolerance)
            if np_item:
                measurements.append(np_item); group.append(np_item)
            for lib in libraries:
                for variant in AFFINE_VARIANTS:
                    item = _measure_affine(lib, variant, x, y, scalar, expected, py_median, warmups, repetitions, tolerance)
                    measurements.append(item); group.append(item)
            champion = _select_champion("affine", size, group)
            if champion: champions.append(champion)

        if "affine_chain" in algorithms:
            expected_chain = python_chain(x, y, z, scalar, chain_b)
            py_chain_median, _, _ = _timed(lambda: python_chain(x, y, z, scalar, chain_b), warmups, repetitions)
            group = []
            np_item = _measure_numpy_chain(x, y, z, scalar, chain_b, expected_chain, py_chain_median, warmups, repetitions, tolerance)
            if np_item:
                measurements.append(np_item); group.append(np_item)
            for lib in libraries:
                for chain_variant in CHAIN_VARIANTS:
                    fused = _measure_chain_fused(lib, chain_variant, x, y, z, scalar, chain_b, expected_chain, py_chain_median, warmups, repetitions, tolerance)
                    measurements.append(fused); group.append(fused)
                for variant in AFFINE_VARIANTS:
                    item = _measure_chain_two_pass(lib, variant, x, y, z, scalar, chain_b, expected_chain, py_chain_median, warmups, repetitions, tolerance)
                    measurements.append(item); group.append(item)
            champion = _select_champion("affine_chain", size, group)
            if champion: champions.append(champion)

        for operation in ("sum", "dot"):
            if operation not in algorithms:
                continue
            expected_scalar = python_sum(x) if operation == "sum" else python_dot(x, y)
            py_fn = (lambda: python_sum(x)) if operation == "sum" else (lambda: python_dot(x, y))
            py_median, _, _ = _timed(py_fn, warmups, repetitions)
            group = []
            np_item = _measure_numpy_reduction(operation, x, y, expected_scalar, py_median, warmups, repetitions, tolerance)
            if np_item:
                measurements.append(np_item); group.append(np_item)
            for lib in libraries:
                for reduction_variant in REDUCTION_VARIANTS:
                    item = _measure_reduction(lib, operation, reduction_variant, x, y, expected_scalar, py_median, warmups, repetitions, tolerance)
                    measurements.append(item); group.append(item)
            champion = _select_champion(operation, size, group)
            if champion: champions.append(champion)

    return AutotuneReport(
        schema_version="omega-polyglot-autotune-v4",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        hardware=hardware_fingerprint(),
        protocol={
            "sizes": list(sizes), "algorithms": list(algorithms), "backends": list(backends),
            "profiles": list(profiles), "warmups": warmups, "repetitions": repetitions,
            "tolerance": tolerance, "seed": seed, "scalar": scalar, "chain_b": chain_b,
            "timing_scope": "prepared zero-copy dispatch plus computation",
            "python_reference": "plain CPython loops",
            "numpy_candidate": "optional preallocated ufunc/dot/sum using zero-copy input views",
        },
        measurements=tuple(measurements),
        champions=tuple(champions),
    )


def save_report(report: AutotuneReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
