import unittest

import numpy as np

from omega_vtp_t import (
    adaptive_dynamic_lift_fit,
    select_by_correlation_with_target,
    select_by_variance,
    tensor_prod_lift,
)


class SparseAdaptiveTensorProdTests(unittest.TestCase):
    def test_variance_selection_keeps_constant_and_removes_dead_feature(self):
        x = np.zeros((16, 2))
        lift = tensor_prod_lift(x, 2)
        sparse = select_by_variance(lift, threshold=1e-12)
        self.assertEqual(sparse.report.original_feature_count, lift.features.shape[1])
        self.assertGreaterEqual(sparse.report.selected_feature_count, 1)
        self.assertIn((0, 0), sparse.alphas)

    def test_correlation_selection_keeps_target_related_feature(self):
        rng = np.random.default_rng(42)
        x = rng.normal(size=(128, 2))
        y = 4 * x[:, 0] ** 2 + 0.01 * rng.normal(size=128)
        lift = tensor_prod_lift(x, 2)
        sparse = select_by_correlation_with_target(lift, y, top_k=3)
        self.assertLessEqual(sparse.report.selected_feature_count, 4)  # top_k + constant
        self.assertIn((2, 0), sparse.alphas)

    def test_adaptive_dynamic_lift_runs_steps(self):
        x = np.linspace(-1, 1, 64).reshape(-1, 1)
        fit = adaptive_dynamic_lift_fit(
            x,
            lambda z: 0.7 * z + 0.1 * z**2,
            min_degree=1,
            max_degree=3,
            residual_tol=1e-14,
            max_features=32,
        )
        self.assertGreaterEqual(len(fit.steps), 1)
        self.assertGreaterEqual(fit.best_degree, 1)
        self.assertLessEqual(fit.best_degree, 3)
        self.assertTrue(fit.stopped_reason in {"residual_tol_reached", "max_degree_reached"})


if __name__ == "__main__":
    unittest.main()
