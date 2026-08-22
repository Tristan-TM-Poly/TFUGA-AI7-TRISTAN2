from fractions import Fraction
import unittest

from omega_zeta_square_t.principal_constraints import all_principal_minor_constraints
from omega_zeta_square_t.symbolic_hankel import tensor_lift_constraint
from omega_zeta_square_t.vtp_bridge import constraint_to_vtp_linear_form, evaluate_vtp_linear_form
from omega_zeta_square_t.xi_constraints import xi_derivative_constraint


class TestPrincipalMinorCompiler(unittest.TestCase):
    def test_size_two_has_all_three_nonempty_principal_minors(self):
        constraints = all_principal_minor_constraints(2, shift=0)
        self.assertEqual(len(constraints), 3)
        self.assertEqual({item.indices for item in constraints}, {(0,), (1,), (0, 1)})
        self.assertTrue(all(item.proves_rh is False for item in constraints))

    def test_size_three_has_seven_principal_minors(self):
        self.assertEqual(len(all_principal_minor_constraints(3, 0)), 7)


class TestXiDerivativeConstraint(unittest.TestCase):
    def test_h2_basic_matches_closed_integer_numerator(self):
        constraint = xi_derivative_constraint(2, 0)
        self.assertEqual(constraint.common_integer_scale, 1440)
        self.assertEqual(constraint.d0_power_denominator, 3)
        terms = {term.monomial: term.coefficient for term in constraint.terms}
        self.assertEqual(
            terms,
            {
                "d0*d4^2": -10,
                "d0*d2*d6": 3,
                "d2^2*d4": 15,
            },
        )
        self.assertFalse(constraint.proves_rh)

    def test_h1_shifted_constraint(self):
        constraint = xi_derivative_constraint(1, 1)
        terms = {term.monomial: term.coefficient for term in constraint.terms}
        # a1^2 - 2a2 = (3 d2^2 - d0 d4)/(12 d0^2)
        self.assertEqual(constraint.common_integer_scale, 12)
        self.assertEqual(terms, {"d0*d4": -1, "d2^2": 3})


class TestExistingVTPBridge(unittest.TestCase):
    def test_r11_linear_form_aligns_with_existing_tensor_prod_lift(self):
        constraint = tensor_lift_constraint(2, 0)
        form = constraint_to_vtp_linear_form(constraint)
        self.assertEqual(form.n_variables, 3)
        self.assertEqual(form.degree, 3)
        self.assertEqual(form.nonzero_feature_count, 3)
        self.assertFalse(form.proves_rh)

        values = [13 / 36, 1 / 36, 0.0]
        observed = evaluate_vtp_linear_form(values, form)
        exact = Fraction(13, 36) ** 2 * Fraction(1, 36) - 4 * Fraction(1, 36) ** 2
        self.assertAlmostEqual(observed, float(exact), places=14)


if __name__ == "__main__":
    unittest.main()
