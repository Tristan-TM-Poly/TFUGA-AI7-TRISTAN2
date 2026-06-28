import unittest

import numpy as np

from omega_vtp_t import (
    MMinusEntry,
    PolynomialODE,
    build_carleman_operator,
    build_mminus_registry,
    compress_operator_svd,
    conservation_check,
    decompose_residuals,
    entry_from_oak_status,
    invariant_report,
    l2_energy,
    positivity_check,
    reciprocal_template,
    ResidualComponent,
    select_ode_tensor_degree,
    solve_lifted_linear,
    standard_auxiliary_templates,
    tensor_prod_lift,
)


class PlusUltraReusableTests(unittest.TestCase):
    def test_residual_decomposition(self):
        report = decompose_residuals(
            [
                ResidualComponent("degree", 1e-4, 1e-3),
                ResidualComponent("boundary", 1e-12, 1e-8),
            ]
        )
        self.assertEqual(report.oak_status, "certified")
        self.assertEqual(report.worst_component, "degree")

    def test_invariant_guards(self):
        before = np.array([1.0, 2.0, 3.0])
        after = np.array([1.0, 2.0, 3.0 + 1e-10])
        checks = [
            conservation_check("l2_energy", l2_energy(before), l2_energy(after), tolerance=1e-6),
            positivity_check(after, tolerance=0.0),
        ]
        report = invariant_report(checks)
        self.assertEqual(report.oak_status, "certified")

    def test_adaptive_de_degree_selection(self):
        ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
        x = np.linspace(-0.5, 0.5, 32).reshape(-1, 1)
        selection = select_ode_tensor_degree(ode, x, min_degree=1, max_degree=4, max_features=16)
        self.assertGreaterEqual(selection.best_degree, 1)
        self.assertGreaterEqual(len(selection.steps), 1)

    def test_low_rank_operator_and_solver(self):
        A = np.diag([-1.0, -2.0, -3.0])
        compressed = compress_operator_svd(A, rank=2)
        self.assertEqual(compressed.rank, 2)
        self.assertLess(compressed.relative_error, 1.0)

        z0 = np.array([[1.0, 0.0, 0.0]])
        traj, report = solve_lifted_linear(z0, A, dt=0.01, steps=3, method="rk4")
        self.assertEqual(traj.shape, (4, 1, 3))
        self.assertGreaterEqual(report.residual_norm, 0.0)

    def test_mminus_and_auxiliary_templates(self):
        entry = entry_from_oak_status(
            "degree_2_logistic",
            "experimental_truncation_residual_high",
            evidence="degree=2 leaves x^3 terms",
        )
        self.assertIsNotNone(entry)
        registry = build_mminus_registry([entry, MMinusEntry("feature_x7", "unstable", 0.7, "large variance", "reduce degree")])
        self.assertEqual(len(registry.entries), 2)

        templates = standard_auxiliary_templates("x")
        names = {template.name for template in templates}
        self.assertIn("sin_cos_closure", names)
        self.assertIn("exp_closure", names)
        self.assertIn("reciprocal_closure", names)
        self.assertIn("x != 0", reciprocal_template("x").constraints)

    def test_carleman_operator_can_be_compressed_after_lift(self):
        ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.5},))
        op = build_carleman_operator(ode, degree=3)
        compressed = compress_operator_svd(op.operator, energy_tol=0.99)
        x = np.array([[0.25]])
        phi = tensor_prod_lift(x, 3).features
        y_full = phi @ op.operator.T
        y_compressed = compressed.apply(phi)
        self.assertEqual(y_full.shape, y_compressed.shape)


if __name__ == "__main__":
    unittest.main()
