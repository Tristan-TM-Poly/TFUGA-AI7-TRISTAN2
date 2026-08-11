from fractions import Fraction
import unittest

from omega_zeta_square_t.adversary import (
    mixed_inverse_moments,
    one_pair_full_hankel_certificate,
    one_pair_full_hankel_determinant,
)
from omega_zeta_square_t.certificates import exact_determinant, exact_hankel_matrix


class TestFiniteOnePairVandermondeTheorem(unittest.TestCase):
    def test_masked_example_full_support_formula_matches_exact_hankel(self):
        reals = [Fraction(5)]
        a = Fraction(1)
        b = Fraction(1)
        moments = mixed_inverse_moments(reals, a, b, 6)
        self.assertEqual(
            one_pair_full_hankel_determinant(reals, a, b, shift=0),
            exact_determinant(exact_hankel_matrix(moments, 3, shift=0)),
        )
        self.assertEqual(
            one_pair_full_hankel_determinant(reals, a, b, shift=1),
            exact_determinant(exact_hankel_matrix(moments, 3, shift=1)),
        )
        self.assertEqual(one_pair_full_hankel_determinant(reals, a, b), -11560)
        self.assertEqual(one_pair_full_hankel_determinant(reals, a, b, shift=1), -115600)

    def test_two_positive_background_atoms_formula_matches_exact_matrix(self):
        reals = [Fraction(2), Fraction(5)]
        a = Fraction(1, 2)
        b = Fraction(3, 2)
        size = len(reals) + 2
        moments = mixed_inverse_moments(reals, a, b, 2 * size)
        for shift in (0, 1):
            expected = one_pair_full_hankel_determinant(reals, a, b, shift=shift)
            observed = exact_determinant(exact_hankel_matrix(moments, size, shift=shift))
            self.assertEqual(observed, expected)
            self.assertLess(expected, 0)

    def test_certificate_reports_full_support_detection_without_rh_promotion(self):
        cert = one_pair_full_hankel_certificate([2, 5], 1, 1)
        self.assertEqual(cert.support_size, 4)
        self.assertTrue(cert.guaranteed_negative)
        self.assertTrue(cert.finite_atomic_model_only)
        self.assertFalse(cert.proves_rh)

    def test_critical_real_pair_has_zero_complex_defect_factor(self):
        det = one_pair_full_hankel_determinant([2, 5], 1, 0)
        self.assertEqual(det, 0)
        cert = one_pair_full_hankel_certificate([2, 5], 1, 0)
        self.assertFalse(cert.guaranteed_negative)

    def test_duplicate_background_atoms_rejected(self):
        with self.assertRaises(ValueError):
            one_pair_full_hankel_determinant([2, 2], 1, 1)


if __name__ == "__main__":
    unittest.main()
