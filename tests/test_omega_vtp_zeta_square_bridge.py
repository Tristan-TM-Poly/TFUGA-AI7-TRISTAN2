from fractions import Fraction
import unittest

from omega_zeta_square_t.symbolic_hankel import tensor_lift_constraint
from omega_zeta_square_t.vtp_bridge import constraint_to_vtp_linear_form, evaluate_vtp_linear_form


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
