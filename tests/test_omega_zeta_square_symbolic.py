from fractions import Fraction
import unittest

from omega_zeta_square_t.symbolic_hankel import (
    evaluate_polynomial,
    hankel_determinant_polynomial,
    newton_power_sum_polynomials,
    tensor_lift_constraint,
)
from omega_zeta_square_t.certificates import exact_determinant, exact_hankel_matrix


class TestNewtonPowerSumCompiler(unittest.TestCase):
    def test_first_four_newton_polynomials(self):
        p = newton_power_sum_polynomials(4)
        values = [Fraction(2), Fraction(3), Fraction(5), Fraction(7)]
        self.assertEqual(evaluate_polynomial(p[0], values), 2)
        self.assertEqual(evaluate_polynomial(p[1], values), -2)
        self.assertEqual(evaluate_polynomial(p[2], values), 5)
        self.assertEqual(evaluate_polynomial(p[3], values), -18)


class TestHankelPolynomialCompiler(unittest.TestCase):
    def test_size_one_constraints(self):
        basic = hankel_determinant_polynomial(1, 0)
        shifted = hankel_determinant_polynomial(1, 1)
        self.assertEqual(basic, {(1,): Fraction(1)})
        self.assertEqual(
            shifted,
            {
                (2, 0): Fraction(1),
                (0, 1): Fraction(-2),
            },
        )

    def test_size_two_basic_closed_form(self):
        poly = hankel_determinant_polynomial(2, 0)
        self.assertEqual(
            poly,
            {
                (2, 1, 0): Fraction(1),
                (1, 0, 1): Fraction(3),
                (0, 2, 0): Fraction(-4),
            },
        )

    def test_size_two_shifted_closed_form(self):
        poly = hankel_determinant_polynomial(2, 1)
        self.assertEqual(
            poly,
            {
                (3, 0, 1, 0): Fraction(-2),
                (2, 2, 0, 0): Fraction(1),
                (2, 0, 0, 1): Fraction(-4),
                (1, 1, 1, 0): Fraction(10),
                (0, 3, 0, 0): Fraction(-4),
                (0, 1, 0, 1): Fraction(8),
                (0, 0, 2, 0): Fraction(-9),
            },
        )

    def test_polynomial_matches_exact_positive_two_atom_hankel(self):
        l1, l2 = Fraction(1, 4), Fraction(1, 9)
        coeffs = [l1 + l2, l1 * l2, Fraction(0)]
        poly = hankel_determinant_polynomial(2, 0)
        symbolic = evaluate_polynomial(poly, coeffs)
        moments = [l1**k + l2**k for k in range(1, 5)]
        direct = exact_determinant(exact_hankel_matrix(moments, 2, shift=0))
        self.assertEqual(symbolic, direct)
        self.assertGreater(symbolic, 0)

    def test_tensor_lift_constraint_is_linear_in_lifted_monomials(self):
        constraint = tensor_lift_constraint(2, 0)
        self.assertFalse(constraint.proves_rh)
        self.assertEqual(constraint.term_count, 3)
        self.assertEqual(constraint.max_total_degree, 3)
        weights = {term.monomial: term.coefficient for term in constraint.terms}
        self.assertEqual(weights, {"a2^2": -4, "a1*a3": 3, "a1^2*a2": 1})

    def test_size_cap_is_explicit(self):
        with self.assertRaises(ValueError):
            hankel_determinant_polynomial(6, 0)


if __name__ == "__main__":
    unittest.main()
