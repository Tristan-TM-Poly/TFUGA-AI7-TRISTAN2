from __future__ import annotations

import unittest

from omega_inverse_problem_t.diagnostics import identifiability_geometry, penrose_residuals, resolution_matrices


class OmegaInverseProblemDiagnosticsTest(unittest.TestCase):
    def test_penrose_conditions_rank_deficient(self) -> None:
        residuals = penrose_residuals([[1.0, 1.0], [2.0, 2.0]])
        for value in residuals.values():
            self.assertLess(value, 1e-8)

    def test_underdetermined_state_resolution_is_projector(self) -> None:
        geometry = resolution_matrices([[1.0, 1.0]])
        state = geometry["state_resolution"]
        observation = geometry["observation_resolution"]
        self.assertAlmostEqual(state[0][0], 0.5, places=7)
        self.assertAlmostEqual(state[0][1], 0.5, places=7)
        self.assertAlmostEqual(state[1][0], 0.5, places=7)
        self.assertAlmostEqual(state[1][1], 0.5, places=7)
        self.assertAlmostEqual(observation[0][0], 1.0, places=7)

    def test_full_rank_square_resolution_is_identity(self) -> None:
        geometry = identifiability_geometry([[2.0, 0.0], [0.0, 3.0]])
        state = geometry["state_resolution"]
        observation = geometry["observation_resolution"]
        for matrix in (state, observation):
            self.assertAlmostEqual(matrix[0][0], 1.0, places=7)
            self.assertAlmostEqual(matrix[1][1], 1.0, places=7)
            self.assertAlmostEqual(matrix[0][1], 0.0, places=7)
            self.assertAlmostEqual(matrix[1][0], 0.0, places=7)
        for value in geometry["penrose_residuals"].values():
            self.assertLess(value, 1e-8)


if __name__ == "__main__":
    unittest.main()
