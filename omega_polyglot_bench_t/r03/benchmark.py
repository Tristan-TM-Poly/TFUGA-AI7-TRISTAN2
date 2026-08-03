"""Benchmarks separating conversion, zero-copy wrapper, and kernel-only costs."""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Iterable
from time import perf_counter_ns

from ..native import NativeVectorAffine
from ..reference import vector_affine_python
from .buffers import NativeAffineLibrary, as_double_array, empty_double_array
from .contracts import ModeMeasurement, SizeBenchmark, ThroughputReport

NativeCall = Callable[[], object]


def _percentile_95(samples: list[int]) -> int:
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _measure(
    call: NativeCall,
    warmups: int,
    repetitions: int,
) -> tuple[int, float, int]:
    for _ in range(warmups):
        call()
    samples: list[int] = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        call()
        samples.append(perf_counter_ns() - start)
    return (
        int(statistics.median(samples)),
        statistics.fmean(samples),
        _percentile_95(samples),
    )


def _max_error(actual: Iterable[float], expected: list[float]) -> float:
    return max(
        (
            abs(float(observed) - float(reference))
            for observed, reference in zip(actual, expected, strict=True)
        ),
        default=0.0,
    )


def _measurement(
    *,
    backend: str,
    mode: str,
    call: NativeCall,
    result: Callable[[], Iterable[float]],
    expected: list[float],
    python_ns: int,
    bytes_per_call: int,
    warmups: int,
    repetitions: int,
    setup_ns: int | None,
    tolerance: float,
    notes: tuple[str, ...],
) -> ModeMeasurement:
    try:
        median_ns, mean_ns, p95_ns = _measure(call, warmups, repetitions)
        max_abs_error = _max_error(result(), expected)
        correct = (
            math.isfinite(max_abs_error)
            and max_abs_error <= tolerance
        )
        speedup = (
            python_ns / median_ns
            if correct and median_ns > 0
            else None
        )
        effective_gib_per_s = (
            (bytes_per_call / median_ns) * (1e9 / (1024**3))
            if correct and median_ns > 0
            else None
        )
        return ModeMeasurement(
            backend=backend,
            mode=mode,
            available=True,
            correct=correct,
            median_ns=median_ns,
            p95_ns=p95_ns,
            mean_ns=mean_ns,
            setup_ns=setup_ns,
            max_abs_error=max_abs_error,
            speedup_vs_python=speedup,
            effective_gib_per_s=effective_gib_per_s,
            repetitions=repetitions,
            notes=notes,
        )
    except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as error:
        return ModeMeasurement(
            backend=backend,
            mode=mode,
            available=False,
            correct=False,
            median_ns=None,
            p95_ns=None,
            mean_ns=None,
            setup_ns=setup_ns,
            max_abs_error=None,
            speedup_vs_python=None,
            effective_gib_per_s=None,
            repetitions=0,
            notes=(str(error),),
        )


def benchmark_throughput(
    *,
    sizes: Iterable[int] = (4_096, 100_000, 1_000_000),
    backends: Iterable[str] = ("c", "cpp", "rust"),
    scalar: float = 1.75,
    seed: int = 1729,
    warmups: int = 3,
    repetitions: int = 15,
    tolerance: float = 1e-12,
) -> ThroughputReport:
    """Compare three execution boundaries for every available native backend.

    ``end_to_end_list`` measures the original convenience API, including list
    conversion, allocation, and output materialization. ``zero_copy_buffer``
    reuses ``array('d')`` payloads but rebuilds ctypes views each call.
    ``kernel_only_prepared`` also reuses those ctypes views, so its timed region
    contains FFI dispatch plus the native kernel.
    """

    if warmups < 0:
        raise ValueError("warmups must be non-negative")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")

    size_reports: list[SizeBenchmark] = []
    for size in sizes:
        if size < 0:
            raise ValueError("sizes must be non-negative")

        generator = random.Random(seed + size)
        x = [generator.uniform(-1.0, 1.0) for _ in range(size)]
        y = [generator.uniform(-1.0, 1.0) for _ in range(size)]
        expected = vector_affine_python(x, y, scalar)
        python_ns, _, _ = _measure(
            lambda: vector_affine_python(x, y, scalar),
            warmups,
            repetitions,
        )

        # Read x and y, write output. This is an effective traffic estimate,
        # not a hardware memory-controller measurement.
        bytes_per_call = size * 8 * 3
        measurements: list[ModeMeasurement] = []

        for backend in tuple(dict.fromkeys(backends)):
            try:
                end_to_end = NativeVectorAffine(backend)
                measurements.append(
                    _measurement(
                        backend=backend,
                        mode="end_to_end_list",
                        call=lambda engine=end_to_end: engine(x, y, scalar),
                        result=lambda engine=end_to_end: engine(x, y, scalar),
                        expected=expected,
                        python_ns=python_ns,
                        bytes_per_call=bytes_per_call,
                        warmups=warmups,
                        repetitions=repetitions,
                        setup_ns=None,
                        tolerance=tolerance,
                        notes=(
                            "includes input conversion, output allocation, and list materialization",
                        ),
                    )
                )
            except (FileNotFoundError, OSError, RuntimeError) as error:
                measurements.append(
                    ModeMeasurement(
                        backend=backend,
                        mode="end_to_end_list",
                        available=False,
                        correct=False,
                        median_ns=None,
                        p95_ns=None,
                        mean_ns=None,
                        setup_ns=None,
                        max_abs_error=None,
                        speedup_vs_python=None,
                        effective_gib_per_s=None,
                        repetitions=0,
                        notes=(str(error),),
                    )
                )
                continue

            setup_start = perf_counter_ns()
            x_buffer = as_double_array(x)
            y_buffer = as_double_array(y)
            output = empty_double_array(size)
            library = NativeAffineLibrary(backend)
            prepared = library.prepare(x_buffer, y_buffer, output)
            setup_ns = perf_counter_ns() - setup_start

            measurements.append(
                _measurement(
                    backend=backend,
                    mode="zero_copy_buffer",
                    call=lambda lib=library, xb=x_buffer, yb=y_buffer, out=output: lib.run_into(
                        xb,
                        yb,
                        scalar,
                        out,
                    ),
                    result=lambda out=output: out,
                    expected=expected,
                    python_ns=python_ns,
                    bytes_per_call=bytes_per_call,
                    warmups=warmups,
                    repetitions=repetitions,
                    setup_ns=setup_ns,
                    tolerance=tolerance,
                    notes=(
                        "persistent array('d') buffers; ctypes views rebuilt per call; no payload copy",
                    ),
                )
            )
            measurements.append(
                _measurement(
                    backend=backend,
                    mode="kernel_only_prepared",
                    call=lambda call=prepared: call.run(scalar),
                    result=lambda call=prepared: call.output,
                    expected=expected,
                    python_ns=python_ns,
                    bytes_per_call=bytes_per_call,
                    warmups=warmups,
                    repetitions=repetitions,
                    setup_ns=setup_ns,
                    tolerance=tolerance,
                    notes=(
                        "persistent buffers and ctypes views; timed region is FFI dispatch plus native kernel",
                    ),
                )
            )

        eligible = [
            item
            for item in measurements
            if item.available
            and item.correct
            and item.speedup_vs_python is not None
        ]
        best = max(eligible, key=lambda item: item.speedup_vs_python) if eligible else None
        size_reports.append(
            SizeBenchmark(
                size=size,
                bytes_per_call=bytes_per_call,
                python_median_ns=python_ns,
                measurements=tuple(measurements),
                best_correct_backend=best.backend if best else None,
                best_correct_mode=best.mode if best else None,
                best_speedup_vs_python=best.speedup_vs_python if best else None,
            )
        )

    return ThroughputReport(
        algorithm="vector_affine_f64",
        scalar=scalar,
        seed=seed,
        warmups=warmups,
        repetitions=repetitions,
        sizes=tuple(size_reports),
    )
