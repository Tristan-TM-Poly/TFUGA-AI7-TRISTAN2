from __future__ import annotations

import json
import math
import unittest

from benchmarks.hgfm_tensorbench import (
    AXIS_SIZE,
    BENCHMARK_ID,
    all_coordinates,
    evaluate_cell,
    run_benchmark,
    solve_exhaustive,
)


class HGFMTensorBenchTests(unittest.TestCase):
    def test_cube_is_exactly_16_cubed(self) -> None:
        coordinates = all_coordinates()
        self.assertEqual(AXIS_SIZE, 16)
        self.assertEqual(len(coordinates), 4096)
        self.assertEqual(len(set(coordinates)), 4096)

    def test_exact_optimum_is_admissible_and_finite(self) -> None:
        optimum, _ = solve_exhaustive()
        self.assertTrue(optimum.admissible)
        self.assertTrue(math.isfinite(optimum.governed_score))
        self.assertEqual(optimum.coordinate, (0, 6, 0))

    def test_oak_quarantines_unauthorized_canonization(self) -> None:
        governed = evaluate_cell((9, 15, 15))
        ungoverned = evaluate_cell((9, 15, 15), use_oak=False)
        self.assertEqual(governed.governed_score, -1.0e12)
        self.assertFalse(ungoverned.admissible)
        self.assertTrue(math.isfinite(ungoverned.governed_score))

    def test_full_benchmark_passes_frozen_checks(self) -> None:
        result = run_benchmark()
        self.assertEqual(result["benchmark_id"], BENCHMARK_ID)
        self.assertEqual(result["status"], "PASS", result["checks"])
        self.assertTrue(all(result["checks"].values()))
        self.assertLess(result["solvers"]["hgfm"]["evaluations"], 4096)
        self.assertEqual(result["solvers"]["hgfm"]["canonical_regret"], 0.0)

    def test_result_is_deterministic_and_strict_json(self) -> None:
        first = run_benchmark()
        second = run_benchmark()
        self.assertEqual(first, second)
        encoded = json.dumps(first, allow_nan=False)
        self.assertGreater(len(encoded), 1000)
        self.assertEqual(len(first["result_sha256"]), 64)

    def test_invalid_coordinate_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_cell((16, 0, 0))


if __name__ == "__main__":
    unittest.main()
