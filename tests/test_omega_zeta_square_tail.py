from fractions import Fraction
import unittest

from omega_zeta_square_t.tail import (
    exact_quadratic_form,
    negative_witness_from_indefinite_2x2,
    polynomial_abs_bound,
    tail_stability_certificate,
)


class TestTailStability(unittest.TestCase):
    def test_exact_2x2_witness(self):
        matrix = [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(0)]]
        witness = negative_witness_from_indefinite_2x2(matrix)
        self.assertEqual(witness, (Fraction(-1), Fraction(2)))
        self.assertEqual(exact_quadratic_form(matrix, witness), -2)

    def test_small_tail_preserves_negative_witness(self):
        matrix = [[Fraction(2), Fraction(0)], [Fraction(0), Fraction(-4)]]
        witness = [Fraction(0), Fraction(1)]
        cert = tail_stability_certificate(
            matrix,
            witness,
            tail_radius_upper=Fraction(1, 10),
            tail_abs_mass_upper=Fraction(1, 20),
        )
        self.assertEqual(cert.finite_quadratic_value, -4)
        self.assertEqual(cert.polynomial_abs_upper, Fraction(1, 10))
        self.assertEqual(cert.tail_quadratic_abs_upper, Fraction(1, 2000))
        self.assertTrue(cert.certified_indefinite_after_tail)
        self.assertGreater(cert.residual_negative_margin, 0)
        self.assertFalse(cert.proves_rh)

    def test_large_uncertainty_does_not_certify(self):
        matrix = [[Fraction(2), Fraction(0)], [Fraction(0), Fraction(-4)]]
        cert = tail_stability_certificate(
            matrix,
            [0, 1],
            tail_radius_upper=2,
            tail_abs_mass_upper=2,
        )
        self.assertFalse(cert.certified_indefinite_after_tail)
        self.assertLess(cert.residual_negative_margin, 0)

    def test_polynomial_bound(self):
        self.assertEqual(
            polynomial_abs_bound([Fraction(1), Fraction(-2), Fraction(3)], Fraction(1, 2)),
            Fraction(11, 4),
        )


if __name__ == "__main__":
    unittest.main()
