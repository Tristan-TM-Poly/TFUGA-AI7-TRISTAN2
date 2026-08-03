"""Unit tests for Ω-TRANSFORM-T."""

from __future__ import annotations

import unittest

import numpy as np

from omega_transform_t import (
    anomaly_score_bench,
    compare_amplitude_vs_fertility_selection,
    compare_fwt_ffwt_thresholding,
    denoise_selection_bench,
    fertility_select_coeffs,
    ffwtn,
    haar_fwt_1d,
    haar_ifwt_1d,
    make_anomaly_signal,
    make_clean_noisy_signal,
    make_coupled_channels,
)


class OmegaTransformTests(unittest.TestCase):
    def test_haar_fwt_reconstructs_exactly(self) -> None:
        x = np.linspace(-1.0, 1.0, 257) + 0.2 * np.sin(np.linspace(0.0, 20.0, 257))
        coeffs = haar_fwt_1d(x)
        xr = haar_ifwt_1d(coeffs)
        err = np.linalg.norm(x - xr) / (np.linalg.norm(x) + 1e-12)
        self.assertLess(err, 1e-10)

    def test_oak_compare_has_sane_metrics(self) -> None:
        t = np.linspace(0.0, 1.0, 512)
        x = np.sin(2 * np.pi * 7 * t) + 0.25 * np.sin(2 * np.pi * 39 * t)
        report = compare_fwt_ffwt_thresholding(x, levels=6, keep_fraction=0.2)
        self.assertIn("fwt", report)
        self.assertIn("ffwt", report)
        self.assertGreaterEqual(report["fwt"]["relative_reconstruction_error"], 0.0)
        self.assertGreaterEqual(report["ffwt"]["relative_reconstruction_error"], 0.0)
        self.assertGreater(report["fwt"]["compression_ratio_estimate"], 1.0)
        self.assertEqual(report["fwt"]["oak_status"], "measured_not_proven")

    def test_fertility_selection_keeps_original_coefficients_shape(self) -> None:
        x = np.sin(np.linspace(0.0, 30.0, 513))
        selected = fertility_select_coeffs(x, levels=7, keep_fraction=0.2)
        xr = haar_ifwt_1d(selected)
        self.assertEqual(xr.shape, x.shape)
        self.assertEqual(selected["selection"], "fertility_select_original_coefficients")

    def test_extreme_selection_bench_reports_both_methods(self) -> None:
        x = np.sin(np.linspace(0.0, 40.0, 512))
        report = compare_amplitude_vs_fertility_selection(x, levels=6, keep_fraction=0.2)
        self.assertIn("amplitude_selection", report)
        self.assertIn("fertility_selection", report)
        self.assertIn("delta_error_amplitude_minus_fertility", report)

    def test_denoise_bench_reports_snr(self) -> None:
        clean, noisy = make_clean_noisy_signal(n=512)
        report = denoise_selection_bench(clean, noisy, levels=6, keep_fraction=0.2)
        self.assertIn("input_snr_db", report)
        self.assertIn("amplitude_selection_snr_db", report)
        self.assertIn("fertility_selection_snr_db", report)

    def test_anomaly_bench_detects_some_expected_overlap(self) -> None:
        x, mask, _ = make_anomaly_signal(n=512)
        report = anomaly_score_bench(x, mask, levels=6, top_fraction=0.1)
        self.assertGreaterEqual(report["topk_expected_overlap"], 0.0)
        self.assertLessEqual(report["topk_expected_overlap"], 1.0)

    def test_ffwtn_multichannel_coherence_separates_noise(self) -> None:
        X = make_coupled_channels(n=1024)
        result = ffwtn(X, levels=7)
        coh = result["coherence_matrix"]
        self.assertGreater(abs(coh[0, 1]), abs(coh[0, 2]))
        self.assertGreater(abs(coh[0, 1]), abs(coh[1, 2]))


if __name__ == "__main__":
    unittest.main()
