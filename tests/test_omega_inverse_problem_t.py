from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omega_inverse_problem_t.core import (
    cycle_consistency_linear,
    gauss_newton_inverse,
    inverse_problem_report,
    least_squares,
    linear_gaussian_posterior,
    matvec,
    route_linear_inverse,
    singular_spectrum,
    tikhonov,
)

ROOT = Path(__file__).resolve().parents[1]


def assert_vec_close(case: unittest.TestCase, got: list[float], expected: list[float], places: int = 6) -> None:
    case.assertEqual(len(got), len(expected))
    for a, b in zip(got, expected):
        case.assertAlmostEqual(a, b, places=places)


class OmegaInverseProblemTest(unittest.TestCase):
    def test_square_full_rank_inverse(self) -> None:
        A = [[2.0, 0.0], [0.0, 4.0]]
        x = [3.0, -2.0]
        y = matvec(A, x)
        assert_vec_close(self, least_squares(A, y), x)
        self.assertEqual(route_linear_inverse(A)["method"], "direct-or-moore-penrose")

    def test_overdetermined_exact_recovery(self) -> None:
        A = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        x = [2.0, -1.0]
        assert_vec_close(self, least_squares(A, matvec(A, x)), x)
        self.assertEqual(route_linear_inverse(A)["method"], "least-squares-moore-penrose")

    def test_underdetermined_minimum_norm_representative(self) -> None:
        A = [[1.0, 1.0]]
        assert_vec_close(self, least_squares(A, [2.0]), [1.0, 1.0])
        route = route_linear_inverse(A)
        self.assertEqual(route["method"], "minimum-norm-moore-penrose")
        self.assertEqual(route["spectrum"]["nullity"], 1)

    def test_rank_deficient_spectrum_and_solution(self) -> None:
        A = [[1.0, 1.0], [2.0, 2.0]]
        spectrum = singular_spectrum(A)
        self.assertEqual(spectrum["rank"], 1)
        self.assertEqual(spectrum["nullity"], 1)
        assert_vec_close(self, least_squares(A, [2.0, 4.0]), [1.0, 1.0], places=5)

    def test_tikhonov_shrinkage(self) -> None:
        A = [[1.0, 0.0], [0.0, 1.0]]
        assert_vec_close(self, tikhonov(A, [2.0, 4.0], 1.0), [1.0, 2.0])

    def test_tikhonov_prior_center(self) -> None:
        A = [[1.0, 0.0], [0.0, 1.0]]
        assert_vec_close(self, tikhonov(A, [2.0, 4.0], 1.0, prior=[10.0, 10.0]), [6.0, 7.0])

    def test_cycle_consistency_full_rank(self) -> None:
        report = cycle_consistency_linear([[2.0, 1.0], [1.0, 3.0]], [1.5, -2.0])
        self.assertLess(report["forward_residual_norm"], 1e-7)
        self.assertLess(report["inverse_residual_norm"], 1e-7)

    def test_nonlinear_inverse_predictor_corrector(self) -> None:
        def f(v: list[float]) -> list[float]:
            return [v[0] ** 2 + v[1], v[0] + 2.0 * v[1]]

        target = f([1.2, -0.3])
        result = gauss_newton_inverse(f, target, [1.0, 0.0], damping=1e-8, tol=1e-10)
        self.assertLess(result.residual_norm, 1e-7)
        assert_vec_close(self, result.x, [1.2, -0.3], places=5)

    def test_linear_gaussian_bayes_scalar(self) -> None:
        posterior = linear_gaussian_posterior([[1.0]], [2.0], [0.0], [[1.0]], [[1.0]])
        assert_vec_close(self, posterior.mean, [1.0])
        self.assertAlmostEqual(posterior.covariance[0][0], 0.5, places=9)

    def test_ill_conditioned_spectrum(self) -> None:
        spectrum = singular_spectrum([[1.0, 0.0], [0.0, 1e-6]], rtol=1e-12)
        self.assertGreater(spectrum["condition_number_nonzero_subspace"], 1e5)

    def test_regularization_router(self) -> None:
        self.assertEqual(route_linear_inverse([[1.0, 0.0], [0.0, 1.0]], regularization=0.1)["method"], "tikhonov")

    def test_oak_report_warns_about_null_space(self) -> None:
        report = inverse_problem_report([[1.0, 1.0]], [2.0])
        self.assertLess(report["residual_norm"], 1e-8)
        self.assertTrue(any("null space" in item for item in report["warnings"]))

    def test_cli_reference_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "report.json"
            md_path = Path(tmp) / "report.md"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "omega_inverse_problem_t.cli",
                    "--preset",
                    "sensor-overdetermined",
                    "--output",
                    str(json_path),
                    "--markdown-output",
                    str(md_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["route"]["method"], "least-squares-moore-penrose")
            self.assertLess(data["residual_norm"], 1e-8)
            self.assertIn("OAK boundary", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
