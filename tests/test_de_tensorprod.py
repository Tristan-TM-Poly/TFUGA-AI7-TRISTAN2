import unittest

import numpy as np

from omega_vtp_t import (
    PolynomialODE,
    build_carleman_operator,
    burgers_rhs_periodic,
    carleman_residual_on_samples,
    laplacian_1d_periodic,
    mass,
    pde_residual_euler,
    reaction_diffusion_rhs,
)


class DETensorProdTests(unittest.TestCase):
    def test_carleman_logistic_coefficients(self):
        # dx/dt = a*x + b*x^2
        a = 0.7
        b = 0.1
        ode = PolynomialODE(dimension=1, coefficients=({(1,): a, (2,): b},))
        op = build_carleman_operator(ode, degree=4)
        idx = {alpha: i for i, alpha in enumerate(op.alphas)}

        self.assertAlmostEqual(op.operator[idx[(1,)], idx[(1,)]], a)
        self.assertAlmostEqual(op.operator[idx[(1,)], idx[(2,)]], b)
        self.assertAlmostEqual(op.operator[idx[(2,)], idx[(2,)]], 2 * a)
        self.assertAlmostEqual(op.operator[idx[(2,)], idx[(3,)]], 2 * b)

    def test_carleman_sample_residual_reports_truncation(self):
        ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
        x = np.linspace(-0.5, 0.5, 32).reshape(-1, 1)
        report = carleman_residual_on_samples(ode, x, degree=2)
        self.assertGreaterEqual(report["residual_term_count"], 1)
        self.assertGreaterEqual(report["sample_relative_residual"], 0.0)

    def test_periodic_laplacian_constant_zero(self):
        u = np.ones(16)
        lap = laplacian_1d_periodic(u, dx=0.1)
        np.testing.assert_allclose(lap, 0.0, atol=1e-12)

    def test_reaction_diffusion_and_mass(self):
        x = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        dx = x[1] - x[0]
        u = np.sin(x)
        rhs = reaction_diffusion_rhs(u, dx=dx, diffusion=0.1, reaction=lambda z: z - z**3)
        self.assertEqual(rhs.shape, u.shape)
        self.assertAlmostEqual(mass(np.ones_like(u), dx), len(u) * dx)

    def test_pde_euler_residual_zero_for_exact_step(self):
        x = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        dx = x[1] - x[0]
        dt = 1e-3
        u = np.sin(x)
        rhs = burgers_rhs_periodic(u, dx=dx, viscosity=0.05)
        u_next = u + dt * rhs
        report = pde_residual_euler(u, u_next, dt=dt, rhs_now=rhs, dx=dx)
        self.assertLess(report.relative_residual, 1e-10)


if __name__ == "__main__":
    unittest.main()
