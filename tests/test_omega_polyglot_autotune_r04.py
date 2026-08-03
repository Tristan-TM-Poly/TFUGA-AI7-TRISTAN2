from __future__ import annotations

import json
import math
from array import array

import pytest

from omega_polyglot_bench_t.r04.autotune import autotune, save_report
from omega_polyglot_bench_t.r04.buffers import bind_buffer, double_array, zeros
from omega_polyglot_bench_t.r04.build import build_native
from omega_polyglot_bench_t.r04.dispatch import AutotunedDispatcher
from omega_polyglot_bench_t.r04.native import AFFINE_VARIANTS, CHAIN_VARIANTS, REDUCTION_VARIANTS, KernelLibrary


@pytest.fixture(scope="session", autouse=True)
def native_build():
    result = build_native(backends=("c", "cpp"), profiles=("portable", "native", "openmp"))
    assert not result["c"]["portable"].startswith("UNAVAILABLE")
    assert not result["cpp"]["portable"].startswith("UNAVAILABLE")
    return result


def vectors(n=257):
    x = double_array((i - 100) / 17 for i in range(n))
    y = double_array((50 - i) / 23 for i in range(n))
    z = double_array((i % 11) / 13 for i in range(n))
    return x, y, z


def test_buffer_contracts():
    a = double_array([1, 2, 3])
    handle = bind_buffer(a, writable=True)
    assert handle.length == 3
    assert handle.owner is a
    with pytest.raises(TypeError):
        bind_buffer([1.0, 2.0])
    with pytest.raises(TypeError):
        bind_buffer(array("f", [1.0]))


def test_affine_variants_are_conformant(native_build):
    x, y, _ = vectors()
    expected = [1.75 * a + b for a, b in zip(x, y, strict=True)]
    for backend in ("c", "cpp"):
        for profile in ("portable", "native", "openmp"):
            lib = KernelLibrary(backend, profile)
            for variant in AFFINE_VARIANTS:
                out = zeros(len(x))
                result = lib.prepare_affine(variant, x, y, out).run(1.75)
                assert result is out
                assert max(abs(a - b) for a, b in zip(out, expected, strict=True)) <= 1e-12


def test_chain_variants_and_fusion(native_build):
    x, y, z = vectors()
    a, b = 1.75, -0.625
    expected = [b * (a * xv + yv) + zv for xv, yv, zv in zip(x, y, z, strict=True)]
    lib = KernelLibrary("c", "openmp")
    for variant in CHAIN_VARIANTS:
        out = zeros(len(x))
        lib.prepare_chain(x, y, z, out, variant=variant).run(a, b)
        assert max(abs(g - e) for g, e in zip(out, expected, strict=True)) <= 1e-12


def test_inplace_reuses_input(native_build):
    x, y, _ = vectors(31)
    original = list(x)
    expected = [2.0 * a + b for a, b in zip(original, y, strict=True)]
    lib = KernelLibrary("cpp", "native")
    result = lib.prepare_inplace(x, y).run(2.0)
    assert result is x
    assert list(x) == pytest.approx(expected)


def test_reductions(native_build):
    x, y, _ = vectors(4097)
    expected_sum = sum(x)
    expected_dot = sum(a * b for a, b in zip(x, y, strict=True))
    lib = KernelLibrary("c", "openmp")
    for variant in REDUCTION_VARIANTS:
        got_sum = lib.prepare_reduction("sum", x, variant=variant).run()
        got_dot = lib.prepare_reduction("dot", x, y, variant=variant).run()
        assert math.isclose(got_sum, expected_sum, rel_tol=1e-12, abs_tol=1e-9)
        assert math.isclose(got_dot, expected_dot, rel_tol=1e-12, abs_tol=1e-9)


def test_autotune_and_dispatch(tmp_path, native_build):
    report = autotune(
        sizes=(16, 256, 4096),
        backends=("c", "cpp"),
        profiles=("portable", "native"),
        algorithms=("affine", "affine_chain", "sum", "dot"),
        warmups=1,
        repetitions=3,
    )
    assert len(report.champions) == 12
    assert all(c.median_ns > 0 for c in report.champions)
    assert any(m.backend == "python" and m.profile == "numpy" for m in report.measurements)
    path = tmp_path / "report.json"
    save_report(report, path)
    payload = json.loads(path.read_text())
    assert payload["claims"]["universal_language_winner"] is False
    dispatcher = AutotunedDispatcher(path)
    x, y, _ = vectors(256)
    out, decision = dispatcher.execute_affine(x, y, 1.25, zeros(len(x)))
    assert decision.algorithm == "affine"
    assert list(out) == pytest.approx([1.25 * a + b for a, b in zip(x, y, strict=True)])


def test_empty_buffers(native_build):
    lib = KernelLibrary("c", "portable")
    empty = double_array([])
    out = zeros(0)
    assert lib.prepare_affine("scalar", empty, empty, out).run(1.0) is out
    assert lib.prepare_reduction("sum", empty).run() == 0.0


def test_robust_aggregation(native_build):
    from omega_polyglot_bench_t.r04.robust import robust_autotune
    payload = robust_autotune(
        trials=2,
        sizes=(16, 256),
        backends=("c", "cpp"),
        profiles=("portable",),
        algorithms=("affine", "dot"),
        warmups=0,
        repetitions=2,
    )
    assert len(payload["champions"]) == 4
    assert all(item["success_rate"] == 1.0 for item in payload["champions"])
    assert payload["claims"]["universal_language_winner"] is False
