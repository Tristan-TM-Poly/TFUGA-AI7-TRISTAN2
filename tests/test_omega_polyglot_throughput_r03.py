"""OAK tests for Ω-POLYGLOT-BENCH-T R0.3."""

from __future__ import annotations

from array import array

import pytest

from omega_polyglot_bench_t.native import build_native
from omega_polyglot_bench_t.r03.benchmark import benchmark_throughput
from omega_polyglot_bench_t.r03.buffers import (
    NativeAffineLibrary,
    as_double_array,
    empty_double_array,
)


@pytest.fixture(scope="module")
def native_backends() -> tuple[str, ...]:
    built = build_native(("c", "cpp", "rust"))
    assert set(built) == {"c", "cpp", "rust"}
    return tuple(sorted(built))


def test_zero_copy_buffer_matches_oracle(native_backends: tuple[str, ...]) -> None:
    for backend in native_backends:
        x = as_double_array([1.0, 2.0, 3.0])
        y = as_double_array([4.0, 5.0, 6.0])
        output = empty_double_array(3)
        library = NativeAffineLibrary(backend)
        library.run_into(x, y, 2.0, output)
        assert list(output) == [6.0, 9.0, 12.0]


def test_prepared_call_reuses_output(native_backends: tuple[str, ...]) -> None:
    for backend in native_backends:
        x = as_double_array([1.0, 2.0, 3.0])
        y = as_double_array([4.0, 5.0, 6.0])
        output = empty_double_array(3)
        prepared = NativeAffineLibrary(backend).prepare(x, y, output)

        first = prepared.run(2.0)
        assert first is output
        assert list(first) == [6.0, 9.0, 12.0]

        second = prepared.run(3.0)
        assert second is output
        assert list(second) == [7.0, 11.0, 15.0]


def test_zero_length_buffers(native_backends: tuple[str, ...]) -> None:
    for backend in native_backends:
        empty = empty_double_array(0)
        library = NativeAffineLibrary(backend)
        library.run_into(empty, empty, 1.0, empty)
        assert list(library.prepare(empty, empty, empty).run(1.0)) == []


def test_invalid_buffer_types_are_rejected(native_backends: tuple[str, ...]) -> None:
    library = NativeAffineLibrary(native_backends[0])
    with pytest.raises(TypeError):
        library.run_into([1.0], array("d", [2.0]), 1.0, array("d", [0.0]))
    with pytest.raises(TypeError):
        library.run_into(array("f", [1.0]), array("d", [2.0]), 1.0, array("d", [0.0]))


def test_mismatched_shapes_are_rejected(native_backends: tuple[str, ...]) -> None:
    library = NativeAffineLibrary(native_backends[0])
    with pytest.raises(ValueError):
        library.run_into(
            array("d", [1.0]),
            array("d", [2.0, 3.0]),
            1.0,
            array("d", [0.0]),
        )


def test_benchmark_preserves_execution_boundaries(
    native_backends: tuple[str, ...],
) -> None:
    report = benchmark_throughput(
        sizes=(128,),
        backends=native_backends,
        warmups=1,
        repetitions=3,
    )
    size = report.sizes[0]
    assert size.size == 128
    assert size.bytes_per_call == 128 * 8 * 3
    assert size.python_median_ns > 0
    assert len(size.measurements) == len(native_backends) * 3
    assert {item.mode for item in size.measurements} == {
        "end_to_end_list",
        "zero_copy_buffer",
        "kernel_only_prepared",
    }
    assert all(item.available for item in size.measurements)
    assert all(item.correct for item in size.measurements)
    assert all(item.max_abs_error == 0.0 for item in size.measurements)
    assert size.best_correct_backend in native_backends
    assert size.best_correct_mode in {
        "end_to_end_list",
        "zero_copy_buffer",
        "kernel_only_prepared",
    }
    assert size.best_speedup_vs_python is not None
    assert report.universal_language_winner_claimed is False
    assert report.energy_measured is False
    assert report.status == "OAK_LOCAL_SOFTWARE_BENCHMARK_ONLY"


def test_report_is_deterministic_except_timings(
    native_backends: tuple[str, ...],
) -> None:
    first = benchmark_throughput(
        sizes=(16,),
        backends=native_backends,
        seed=99,
        warmups=0,
        repetitions=1,
    )
    second = benchmark_throughput(
        sizes=(16,),
        backends=native_backends,
        seed=99,
        warmups=0,
        repetitions=1,
    )
    assert first.algorithm == second.algorithm
    assert first.seed == second.seed
    assert first.sizes[0].size == second.sizes[0].size
    assert [item.backend for item in first.sizes[0].measurements] == [
        item.backend for item in second.sizes[0].measurements
    ]
    assert [item.mode for item in first.sizes[0].measurements] == [
        item.mode for item in second.sizes[0].measurements
    ]
