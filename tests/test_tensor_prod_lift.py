import math
import unittest

import numpy as np

from omega_vtp_t import (
    feature_count,
    fit_linear_operator,
    multi_indices,
    polynomial_eval_from_lift,
    tensor_prod_lift,
)
from omega_vtp_t.oakbench_vtp import oak_polynomial_exactness_demo


class TensorProdLiftTests(unittest.TestCase):
    def test_feature_count(self):
        self.assertEqual(feature_count(2, 3), math.comb(5, 3))
        self.assertEqual(feature_count(3, 2), 10)

    def test_multi_indices_count(self):
        alphas = multi_indices(3, 2)
        self.assertEqual(len(alphas), 10)
        self.assertIn((0, 0, 0), alphas)
        self.assertIn((2, 0, 0), alphas)
        self.assertIn((1, 1, 0), alphas)

    def test_polynomial_eval_exact(self):
        v = np.array([[2.0, 3.0], [1.0, -1.0]])
        coeffs = {
            (0, 0): 2.0,
            (2, 0): 3.0,
            (1, 1): 5.0,
            (0, 3): -7.0,
        }
        got = polynomial_eval_from_lift(v, 3, coeffs)
        expected = 3 * v[:, 0] ** 2 + 5 * v[:, 0] * v[:, 1] - 7 * v[:, 1] ** 3 + 2
        np.testing.assert_allclose(got, expected, rtol=0, atol=1e-12)

    def test_fit_linear_operator_identity(self):
        x = np.linspace(-1, 1, 21).reshape(-1, 1)
        z = tensor_prod_lift(x, 3).features
        fit = fit_linear_operator(z, z)
        self.assertEqual(fit.operator.shape, (z.shape[1], z.shape[1]))
        self.assertLess(fit.report.relative_residual, 1e-12)

    def test_oak_polynomial_demo(self):
        report = oak_polynomial_exactness_demo()
        self.assertEqual(report["oak_status"], "certified")


if __name__ == "__main__":
    unittest.main()
