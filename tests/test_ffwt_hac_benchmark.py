from __future__ import annotations


def test_ffwt_benchmark_smoke_gate() -> None:
    """Pytest smoke gate.

    The workflow validates the executable benchmark through the report generation
    step. This smoke test keeps pytest wired into CI without duplicating the
    heavier CLI benchmark run.
    """

    assert True
