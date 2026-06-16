#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
PROTOTYPES_DIR = ROOT / "prototypes"
for folder in (CORE_DIR, PROTOTYPES_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from jkd_fusion_strike import MAX_NULL_PERMUTATIONS, jkd_strike
from jkd_tensor_inputs import simulate_chess_tensor, simulate_raman_tensor


class JKDFusionStrikeTests(unittest.TestCase):
    def test_score_is_bounded_and_positive_for_aberrant_tensor(self):
        tensor = np.array([1e9, -1e9, 1e-9, -1e-9, 0.0, 7.0, -3.0, 2.0])
        result = jkd_strike(tensor, permutation_checks=8)
        self.assertGreaterEqual(result["oak_score"], 0.0)
        self.assertLessEqual(result["oak_score"], 100.0)
        self.assertIn(result["verdict"], {"CANON", "FERTILE", "M_MINUS"})

    def test_permutation_budget_is_capped(self):
        tensor = simulate_raman_tensor(points=1024, noise_level=0.08)
        result = jkd_strike(tensor, permutation_checks=10_000)
        control = result["permutation_control"]
        self.assertEqual(control["used_permutations"], MAX_NULL_PERMUTATIONS)
        self.assertEqual(control["requested_permutations"], 10_000)

    def test_large_tensor_uses_downsampled_null_control(self):
        rng = np.random.default_rng(2026)
        tensor = rng.normal(size=20000)
        result = jkd_strike(tensor, permutation_checks=50)
        control = result["permutation_control"]
        self.assertTrue(control["downsampled"])
        self.assertLess(control["used_permutations"], 50)
        self.assertLessEqual(control["null_signal_size"], 4096)

    def test_chess_chaos_is_not_auto_canonized(self):
        chaotic = simulate_chess_tensor("chaotic")
        result = jkd_strike(chaotic, permutation_checks=24)
        self.assertNotEqual(result["verdict"], "CANON")

    def test_structured_raman_and_chess_return_valid_oak_objects(self):
        raman = simulate_raman_tensor(points=1024, noise_level=0.08)
        chess = simulate_chess_tensor("initial")
        for tensor in (raman, chess):
            result = jkd_strike(tensor, permutation_checks=16)
            self.assertIn(result["verdict"], {"CANON", "FERTILE", "M_MINUS"})
            self.assertGreaterEqual(result["oak_score"], 0.0)
            self.assertLessEqual(result["oak_score"], 100.0)
            self.assertIn("permutation_control", result)
            self.assertIn("signatures_cvcd", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
