from __future__ import annotations

import math

from sage_tristan.omega_ffwt import (
    cvcd_summary,
    energy_concentration,
    generate_signal,
    haar_ffwt_candidate,
    inverse_haar_ffwt_candidate,
    real_hac,
    reconstruction_error,
    run_minimal_benchmark,
)


def test_generate_signal_is_deterministic() -> None:
    first = generate_signal("white_noise", length=32, seed=123)
    second = generate_signal("white_noise", length=32, seed=123)
    assert first == second
    assert len(first) == 32


def test_haar_candidate_reconstructs_sine() -> None:
    signal = generate_signal("sine", length=64, seed=7)
    coeffs = haar_ffwt_candidate(signal)
    reconstructed = inverse_haar_ffwt_candidate(coeffs)
    assert reconstruction_error(signal, reconstructed) < 1e-12


def test_energy_concentration_is_bounded() -> None:
    signal = generate_signal("fractal_like", length=64, seed=7)
    coeffs = haar_ffwt_candidate(signal)
    concentration = energy_concentration(coeffs, keep_ratio=0.10)
    assert 0.0 <= concentration <= 1.0


def test_real_hac_identical_signal_has_unit_coherence() -> None:
    signal = generate_signal("chirp", length=64, seed=7)
    hac = real_hac(signal, signal)
    assert math.isclose(hac["correlation"], 1.0, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(hac["coherence"], 1.0, rel_tol=1e-12, abs_tol=1e-12)


def test_cvcd_summary_contains_oak_and_residues() -> None:
    signal = generate_signal("step", length=64, seed=7)
    summary = cvcd_summary("step", signal)
    assert summary["oak_level"] == "OAK-3 candidate"
    assert "reconstruction_rmse" in summary["residues"]
    assert "baseline_delta" in summary["invariants"]
    assert "oak_score" in summary


def test_minimal_benchmark_runs_all_synthetic_signals() -> None:
    report = run_minimal_benchmark(length=64, seed=7)
    assert report["module"] == "omega_ffwt_hac_cvcd"
    assert len(report["results"]) == 6
    assert report["aggregate"]["claim_boundary"] == "synthetic signals only; no universal superiority claim"
