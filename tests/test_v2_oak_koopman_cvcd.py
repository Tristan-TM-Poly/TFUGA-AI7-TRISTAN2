import unittest

import numpy as np

from omega_vtp_t import (
    chebyshev_lift,
    closure_residual,
    fit_koopman_tensorprod,
    select_cvcd_features,
    tensor_prod_lift,
    train_test_koopman_oak,
)


class V2OAKKoopmanCVCDTests(unittest.TestCase):
    def test_chebyshev_lift_shape(self):
        x = np.linspace(-1, 1, 5).reshape(-1, 1)
        lift = chebyshev_lift(x, 3, domain=([-1.0], [1.0]))
        self.assertEqual(lift.features.shape, (5, 4))
        np.testing.assert_allclose(lift.features[:, 0], 1.0)

    def test_koopman_exact_linear_scaling(self):
        x = np.linspace(-1, 1, 64).reshape(-1, 1)
        y = 0.5 * x
        fit = fit_koopman_tensorprod(x, y, degree=3, lift="monomial")
        self.assertLess(fit.fit.report.relative_residual, 1e-12)

    def test_closure_report(self):
        x = np.linspace(-1, 1, 64).reshape(-1, 1)
        y = 0.5 * x
        report = closure_residual(x, y, degree=3)
        self.assertGreater(report.closure_coefficient, 0.999999)

    def test_train_test_oak(self):
        x = np.linspace(-1, 1, 128).reshape(-1, 1)
        y = 0.5 * x
        report = train_test_koopman_oak(x, y, degree=3, lift="monomial", seed=1)
        self.assertLess(report.test_relative_residual, 1e-12)

    def test_cvcd_selection(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=(128, 2))
        y = 3 * x[:, 0] ** 2 + 0.01 * rng.normal(size=128)
        lift = tensor_prod_lift(x, degree=2)
        selection = select_cvcd_features(lift, y, top_k=3)
        self.assertIn((2, 0), selection.alphas)
        self.assertGreaterEqual(selection.features.shape[1], 3)


if __name__ == "__main__":
    unittest.main()
