"""Unit tests for Ω-TRANSFORM-T.

These tests intentionally verify conservative OAK properties:
- exact Haar reconstruction when no coefficients are removed;
- sparse OAK reports have sane metrics;
- FFWT-N multichannel coherence detects related channels more than noise.
"""

from __future__ import annotations

import unittest

import numpy as np

from omega_transform_t import (
    compare_fwt_ffwt_thresholding,
    ffwtn,
    haar_fwt_1d,
    haar_ifwt_1d,
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

    def test_ffwtn_multichannel_coherence_separates_noise(self) -> None:
        rng = np.random.default_rng(123)
        t = np.linspace(0.0, 1.0, 1024)
        base = np.sin(2 * np.pi * 13 * t) + 0.25 * np.sin(2 * np.pi * 55 * t)
        x0 = base + 0.02 * rng.normal(size=t.size)
        x1 = 0.9 * base + 0.02 * rng.normal(size=t.size)
        x2 = rng.normal(size=t.size)
        result = ffwtn(np.vstack([x0, x1, x2]), levels=7)
        coh = result["coherence_matrix"]
        self.assertGreater(abs(coh[0, 1]), abs(coh[0, 2]))
        self.assertGreater(abs(coh[0, 1]), abs(coh[1, 2]))


if __name__ == "__main__":
    unittest.main()
