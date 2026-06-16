#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "core", ROOT / "prototypes"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from omega_ffwt_core import extract_ffwt_signatures, haar_fractal_transform, inverse_haar_fractal_transform
import omega_max_benchmark as bench


class FFWTCoreTests(unittest.TestCase):
    def test_reconstruction(self):
        rng = np.random.default_rng(123)
        t = np.linspace(0.0, 4.0, 2048)
        signal = np.sin(2.0 * np.pi * 3.0 * t) + 0.25 * np.sin(2.0 * np.pi * 11.0 * t)
        signal = signal + rng.normal(0.0, 0.005, size=t.size)
        coeffs = haar_fractal_transform(signal, max_levels=8, adaptive=False)
        recon = inverse_haar_fractal_transform(coeffs)
        original = signal[: coeffs["working_length"]]
        rel_error = np.linalg.norm(recon - original) / (np.linalg.norm(original) + 1e-12)
        self.assertLess(rel_error, 1e-10)

    def test_signatures(self):
        t = np.linspace(0.0, 6.0, 1024)
        signal = np.exp(-0.4 * t) * np.cos(5.0 * t)
        signatures = extract_ffwt_signatures(haar_fractal_transform(signal, max_levels=7, adaptive=True))
        for key in [
            "ffwt_total_energy",
            "ffwt_residual_ratio",
            "ffwt_energy_entropy",
            "ffwt_dominant_level",
            "fractal_ratio",
            "ffwt_mean_adjacent_coherence",
            "ffwt_reconstruction_energy_error",
        ]:
            self.assertIn(key, signatures)
            self.assertTrue(np.isfinite(signatures[key]))
        self.assertGreater(signatures["ffwt_total_energy"], 0.0)
        self.assertLess(signatures["ffwt_reconstruction_energy_error"], 1e-10)


class OAKBenchmarkTests(unittest.TestCase):
    def setUp(self):
        bench.RNG = np.random.default_rng(42)

    def test_b1_canon(self):
        result = bench.run_b1(np.linspace(0.0, 12.0, 2400))
        self.assertEqual(result.verdict, "CANON")
        self.assertGreaterEqual(result.oak_score, 80.0)
        self.assertLess(result.errors["gamma_rel_error"], 0.10)
        self.assertLess(result.errors["w0_rel_error"], 0.05)
        self.assertIn("ffwt_dominant_level", result.extracted)

    def test_b2_canon(self):
        result = bench.run_b2(np.linspace(0.0, 12.0, 2400))
        self.assertEqual(result.verdict, "CANON")
        self.assertGreaterEqual(result.oak_score, 80.0)
        self.assertLess(result.errors["omega0_rel_error"], 0.05)
        self.assertLess(result.errors["wd_rel_error"], 0.05)
        self.assertIn("ffwt_mean_adjacent_coherence", result.extracted)

    def test_b3_canon_and_tracks_candidate(self):
        result = bench.run_b3(np.linspace(-12.0, 12.0, 2400), 2.0)
        self.assertEqual(result.verdict, "CANON")
        self.assertGreaterEqual(result.oak_score, 80.0)
        self.assertLess(result.errors["D_rel_error"], 0.15)
        self.assertIn("D_ffwt_candidate", result.extracted)
        self.assertIn("D_ffwt_candidate_rel_error", result.errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
