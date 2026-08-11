from fractions import Fraction
import unittest

from omega_zeta_square_t.adversary import (
    centered_pair_hankel2_determinant,
    conjugate_pair_hankel2_determinant,
    conjugate_pair_inverse_moments,
    first_exact_stieltjes_violation,
    lambda_pair_from_beta_gamma,
    mixed_inverse_moments,
)
from omega_zeta_square_t.certificates import exact_determinant, exact_hankel_matrix


class TestOffLineConjugatePairIdentity(unittest.TestCase):
    def test_pair_hankel_identity_exact(self):
        a, b = Fraction(1), Fraction(1)
        moments = conjugate_pair_inverse_moments(a, b, 4)
        h0 = exact_hankel_matrix(moments, size=2, shift=0)
        self.assertEqual(exact_determinant(h0), conjugate_pair_hankel2_determinant(a, b))
        self.assertEqual(exact_determinant(h0), Fraction(-8))

    def test_centered_formula_matches_lambda_formula(self):
        beta = Fraction(3, 5)
        gamma = Fraction(2)
        a, b = lambda_pair_from_beta_gamma(beta, gamma)
        self.assertEqual(
            centered_pair_hankel2_determinant(beta, gamma),
            conjugate_pair_hankel2_determinant(a, b),
        )
        self.assertLess(centered_pair_hankel2_determinant(beta, gamma), 0)

    def test_critical_line_degenerates_to_zero_pair_defect(self):
        beta = Fraction(1, 2)
        gamma = Fraction(2)
        a, b = lambda_pair_from_beta_gamma(beta, gamma)
        self.assertEqual(b, 0)
        self.assertEqual(a, Fraction(1, 4))
        self.assertEqual(centered_pair_hankel2_determinant(beta, gamma), 0)


class TestFiniteMaskingDepth(unittest.TestCase):
    def test_isolated_pair_detected_at_size_two(self):
        moments = conjugate_pair_inverse_moments(1, 1, 6)
        depth = first_exact_stieltjes_violation(moments, max_hankel_size=3)
        self.assertTrue(depth.detected)
        self.assertEqual(depth.first_hankel_size, 2)
        self.assertFalse(depth.proves_rh)

    def test_positive_background_can_mask_size_two_but_size_three_detects(self):
        moments = mixed_inverse_moments([5], 1, 1, 6)
        h0_2 = exact_determinant(exact_hankel_matrix(moments, 2, shift=0))
        h1_2 = exact_determinant(exact_hankel_matrix(moments, 2, shift=1))
        self.assertEqual(h0_2, 222)
        self.assertEqual(h1_2, 784)
        depth = first_exact_stieltjes_violation(moments, max_hankel_size=3)
        self.assertTrue(depth.detected)
        self.assertEqual(depth.first_hankel_size, 3)
        h0_3 = exact_determinant(exact_hankel_matrix(moments, 3, shift=0))
        h1_3 = exact_determinant(exact_hankel_matrix(moments, 3, shift=1))
        self.assertEqual(h0_3, -11560)
        self.assertEqual(h1_3, -115600)


if __name__ == "__main__":
    unittest.main()
