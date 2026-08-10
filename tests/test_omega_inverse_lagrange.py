from __future__ import annotations

import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import omega_inverse_compiler as core  # noqa: E402
import omega_inverse_lagrange as lagrange  # noqa: E402


class OmegaInverseLagrangeTest(unittest.TestCase):
    def test_three_engines_agree_on_reference_families(self) -> None:
        examples = [
            [0, 1, 1],
            core.preset_coefficients("exp-minus-one", 8),
            core.preset_coefficients("lambert", 8),
            core.preset_coefficients("sin", 8),
            core.preset_coefficients("mobius", 8),
            [0, 2, 3, 5, 7, 11, 13, 17, 19],
        ]
        for coeffs in examples:
            with self.subTest(coeffs=coeffs[:4]):
                report = lagrange.cross_validate_three_engines(coeffs, 8)
                self.assertTrue(report["all_equal"])

    def test_lagrange_matches_deterministic_rational_polynomial_sweep(self) -> None:
        rng = random.Random(20260810)
        for case in range(20):
            order = 7
            linear = rng.choice([-3, -2, -1, 1, 2, 3])
            coeffs = [Fraction(0), Fraction(linear)]
            for _ in range(2, order + 1):
                coeffs.append(Fraction(rng.randint(-4, 4), rng.randint(1, 5)))
            with self.subTest(case=case, linear=linear):
                triangular = core.revert_series(coeffs, order)
                newton = core.revert_series_newton(coeffs, order)
                lagrange_result = lagrange.revert_series_lagrange(coeffs, order)
                self.assertEqual(triangular, newton)
                self.assertEqual(triangular, lagrange_result)
                validation = core.validate_reversion(coeffs, lagrange_result, order)
                self.assertTrue(validation["left_exact_through_order"])
                self.assertTrue(validation["right_exact_through_order"])

    def test_lagrange_quadratic_returns_signed_catalan_prefix(self) -> None:
        result = lagrange.revert_series_lagrange([0, 1, 1], 8)
        self.assertEqual(
            result,
            [
                Fraction(0),
                Fraction(1),
                Fraction(-1),
                Fraction(2),
                Fraction(-5),
                Fraction(14),
                Fraction(-42),
                Fraction(132),
                Fraction(-429),
            ],
        )

    def test_lagrange_refuses_critical_taylor_case(self) -> None:
        with self.assertRaises(ValueError):
            lagrange.revert_series_lagrange([0, 0, 1], 6)


if __name__ == "__main__":
    unittest.main()
