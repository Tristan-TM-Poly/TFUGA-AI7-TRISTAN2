from __future__ import annotations

import pytest

from omega_polyglot_bench_t.benchmark import benchmark_backends, select_backend
from omega_polyglot_bench_t.contracts import BackendMeasurement
from omega_polyglot_bench_t.reference import vector_affine_python


def measurement(name: str, median_ns: int, *, correct: bool = True) -> BackendMeasurement:
    return BackendMeasurement(
        backend=name,
        available=True,
        correct=correct,
        cold_ns=median_ns + 10,
        median_ns=median_ns,
        p95_ns=median_ns + 5,
        mean_ns=float(median_ns),
        max_abs_error=0.0,
        repetitions=5,
    )


def test_python_reference_vector_affine() -> None:
    assert vector_affine_python([1.0, -2.0], [0.5, 3.0], 2.0) == [2.5, -1.0]


def test_python_reference_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same length"):
        vector_affine_python([1.0], [], 2.0)


def test_python_only_benchmark_is_deterministic_and_selectable() -> None:
    first = benchmark_backends(size=128, seed=41, warmups=0, repetitions=3, backends=("python",))
    second = benchmark_backends(size=128, seed=41, warmups=0, repetitions=3, backends=("python",))
    assert first.algorithm == second.algorithm == "vector_affine_f64"
    assert first.selected_backend == second.selected_backend == "python"
    assert first.measurements[0].correct is True
    assert first.measurements[0].max_abs_error == 0.0
    assert first.status == "OAK_SOFTWARE_BENCHMARK_ONLY"


def test_selector_rejects_faster_incorrect_backend() -> None:
    selected = select_backend(
        (
            measurement("python", 200),
            measurement("c", 50, correct=False),
            measurement("rust", 80),
        )
    )
    assert selected == "rust"


def test_invalid_benchmark_arguments_are_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        benchmark_backends(repetitions=0, backends=("python",))
    with pytest.raises(ValueError, match="unknown backends"):
        benchmark_backends(backends=("fortran",))
