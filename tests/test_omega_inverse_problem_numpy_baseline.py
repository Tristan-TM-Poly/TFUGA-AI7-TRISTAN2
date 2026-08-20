from __future__ import annotations

import unittest

import numpy as np

from omega_inverse_problem_t.core import pseudoinverse


class OmegaInverseProblemNumpyBaselineTest(unittest.TestCase):
    def assert_matrix_close(self, got: list[list[float]], expected: np.ndarray, tol: float = 1e-6) -> None:
        error = np.linalg.norm(np.asarray(got, dtype=float) - expected)
        self.assertLess(error, tol, msg=f"matrix error {error}")

    def test_random_full_rank_geometries_match_numpy_pinv(self) -> None:
        rng = np.random.default_rng(20260810)
        for rows, cols in [(2, 2), (3, 2), (2, 3), (4, 3), (3, 4)]:
            for _ in range(8):
                matrix = rng.normal(size=(rows, cols))
                ours = pseudoinverse(matrix.tolist(), rtol=1e-10)
                reference = np.linalg.pinv(matrix, rcond=1e-10)
                self.assert_matrix_close(ours, reference)

    def test_rank_deficient_geometries_match_numpy_pinv(self) -> None:
        matrices = [
            np.array([[1.0, 1.0], [2.0, 2.0]]),
            np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]]),
            np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 2.0]]),
        ]
        for matrix in matrices:
            ours = pseudoinverse(matrix.tolist(), rtol=1e-10)
            reference = np.linalg.pinv(matrix, rcond=1e-10)
            self.assert_matrix_close(ours, reference, tol=1e-5)


if __name__ == "__main__":
    unittest.main()
