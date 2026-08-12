from __future__ import annotations

import unittest

from omega_compute_physics_t.optimization_roi import (
    OptimizationOpportunity,
    rank_optimization_roi,
    score_opportunity,
)


class TestOptimizationROI(unittest.TestCase):
    def test_high_debt_requests_remeasurement(self) -> None:
        row = score_opportunity(OptimizationOpportunity(
            repository="org/repo",
            node="m.py:f",
            impact_score=2.0,
            estimated_relative_savings=0.5,
            usage_weight=100.0,
            engineering_effort_hours=2.0,
            confidence_debt=0.8,
        ))
        self.assertTrue(row.remeasure_first)
        self.assertEqual(row.priority, "remeasure-before-optimization")

    def test_rank_prefers_large_evidence_adjusted_value(self) -> None:
        rows = rank_optimization_roi([
            OptimizationOpportunity("org/repo", "a.py:a", 1.0, 0.20, 10.0, 4.0, 0.1),
            OptimizationOpportunity("org/repo", "b.py:b", 2.0, 0.40, 100.0, 2.0, 0.1),
        ])
        self.assertEqual(rows[0].node, "b.py:b")
        self.assertGreater(rows[0].roi_proxy, rows[1].roi_proxy)


if __name__ == "__main__":
    unittest.main()
