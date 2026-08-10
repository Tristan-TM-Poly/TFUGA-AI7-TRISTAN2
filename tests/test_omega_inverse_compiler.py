from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import omega_inverse_compiler as inv  # noqa: E402


class OmegaInverseCompilerTest(unittest.TestCase):
    def test_quadratic_reversion_is_catalan_and_exact_both_directions(self) -> None:
        report = inv.compile_inverse([0, 1, 1], order=8, system_id="quadratic")
        self.assertEqual(report.status, "regular")
        self.assertEqual(
            report.inverse_coefficients,
            ["0", "1", "-1", "2", "-5", "14", "-42", "132", "-429"],
        )
        self.assertTrue(report.direct_newton_agreement)
        self.assertTrue(report.validation["left_exact_through_order"])
        self.assertTrue(report.validation["right_exact_through_order"])
        self.assertIsNotNone(report.algebraic_candidate)
        self.assertIsNotNone(report.coefficient_ratio_candidate)

    def test_exp_minus_one_reverts_to_log_one_plus_z(self) -> None:
        coeffs = [Fraction(0)] + [Fraction(1, math.factorial(n)) for n in range(1, 9)]
        result = inv.revert_series(coeffs, 8)
        expected = [Fraction(0)] + [Fraction((-1) ** (n + 1), n) for n in range(1, 9)]
        self.assertEqual(result, expected)
        self.assertEqual(result, inv.revert_series_newton(coeffs, 8))

    def test_lambert_series(self) -> None:
        coeffs = [Fraction(0)] + [Fraction(1, math.factorial(n - 1)) for n in range(1, 8)]
        result = inv.revert_series(coeffs, 7)
        expected = [Fraction(0)] + [
            Fraction((-n) ** (n - 1), math.factorial(n)) for n in range(1, 8)
        ]
        self.assertEqual(result, expected)

    def test_sine_reverts_to_arcsine_first_terms(self) -> None:
        coeffs = inv.preset_coefficients("sin", 9)
        result = inv.revert_series(coeffs, 9)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 0)
        self.assertEqual(result[3], Fraction(1, 6))
        self.assertEqual(result[5], Fraction(3, 40))
        self.assertEqual(result[7], Fraction(5, 112))
        self.assertEqual(result[9], Fraction(35, 1152))

    def test_mobius_is_recognized_as_exact_rational_candidate(self) -> None:
        report = inv.compile_inverse(inv.preset_coefficients("mobius", 9), order=9)
        self.assertIsNotNone(report.rational_candidate)
        self.assertEqual(report.rational_candidate["numerator"], ["0", "1"])
        self.assertEqual(report.rational_candidate["denominator"], ["1", "1"])

    def test_quadratic_critical_value_radius_proxy(self) -> None:
        analysis = inv.critical_point_analysis([0, 1, 1])
        self.assertEqual(len(analysis["critical_points_of_truncated_polynomial"]), 1)
        point = analysis["critical_points_of_truncated_polynomial"][0]
        self.assertAlmostEqual(point["x"]["re"], -0.5, places=12)
        self.assertAlmostEqual(point["critical_value"]["re"], -0.25, places=12)
        self.assertAlmostEqual(analysis["critical_value_radius_proxy"], 0.25, places=12)

    def test_critical_square_switches_to_two_puiseux_branches(self) -> None:
        report = inv.compile_inverse([0, 0, 1], order=6)
        self.assertEqual(report.status, "critical")
        self.assertEqual(report.multiplicity, 2)
        self.assertIsNone(report.inverse_coefficients)
        self.assertEqual(report.puiseux["multiplicity"], 2)
        c1 = [branch["coefficients_c_k"][1] for branch in report.puiseux["branches"]]
        self.assertAlmostEqual(c1[0]["re"], 1.0, places=12)
        self.assertAlmostEqual(c1[1]["re"], -1.0, places=12)
        self.assertAlmostEqual(c1[0]["im"], 0.0, places=12)
        self.assertAlmostEqual(c1[1]["im"], 0.0, places=12)

    def test_inverse_derivative_jet_matches_known_formulas(self) -> None:
        report = inv.compile_inverse([0, 2, 3, 5], order=3)
        jet = [Fraction(x) for x in report.inverse_derivative_jet]
        self.assertEqual(jet[1], Fraction(1, 2))
        self.assertEqual(jet[2], Fraction(-3, 4))
        self.assertEqual(jet[3], Fraction(3, 2))

    def test_pade_matches_all_fitted_coefficients(self) -> None:
        coeffs = [Fraction(0), 1, -1, 1, -1, 1, -1]
        candidate = inv.pade(coeffs, 1, 1)
        self.assertIsNotNone(candidate)
        p, q = candidate
        self.assertEqual(p, [0, 1])
        self.assertEqual(q, [1, 1])
        self.assertEqual(inv.series_divide(p, q, 6), coeffs)

    def test_shift_metadata_is_preserved(self) -> None:
        report = inv.compile_inverse([0, 3, 1], order=4, x0="5/2", y0="-7/3")
        self.assertEqual(report.x0, "5/2")
        self.assertEqual(report.y0, "-7/3")

    def test_degenerate_series_is_reported_not_inverted(self) -> None:
        report = inv.compile_inverse([0], order=4)
        self.assertEqual(report.status, "degenerate")
        self.assertIsNone(report.inverse_coefficients)
        self.assertIsNone(report.puiseux)

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "quadratic.json"
            out_md = Path(tmpdir) / "quadratic.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "omega_inverse_compiler.py"),
                    "--preset",
                    "quadratic",
                    "--order",
                    "7",
                    "--output",
                    str(out_json),
                    "--markdown-output",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"status": "regular"', result.stdout)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())
            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(data["inverse_coefficients"][5], "14")
            self.assertIn("OAK boundary", out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
