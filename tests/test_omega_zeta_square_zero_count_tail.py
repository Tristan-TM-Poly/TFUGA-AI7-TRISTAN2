import math
import unittest

from omega_zeta_square_t.zero_count_tail import (
    ZeroCountEnvelope,
    reciprocal_tail_bound,
    zero_count_upper,
)


class TestZeroCountTailCompiler(unittest.TestCase):
    def test_closed_tail_formula(self):
        envelope = ZeroCountEnvelope(
            a_t_log_t=1.0,
            b_t=2.0,
            c_log_t=3.0,
            d_const=4.0,
            valid_from=10.0,
            source_id="synthetic-test-envelope",
            certified=True,
        )
        T = 20.0
        bound = reciprocal_tail_bound(T, envelope)
        expected = (
            (2.0 * (math.log(T) + 1.0) + 4.0) / T
            + (3.0 * (math.log(T) + 0.5) + 4.0) / (T * T)
        )
        self.assertAlmostEqual(bound.absolute_mass_upper, expected, places=14)
        self.assertAlmostEqual(bound.radius_upper, 1.0 / 400.0, places=16)
        self.assertTrue(bound.analytically_usable_for_r9)
        self.assertFalse(bound.proves_rh)

    def test_uncertified_source_remains_conditional(self):
        envelope = ZeroCountEnvelope(
            1.0, 0.0, 0.0, 0.0, 10.0, "unverified-envelope", certified=False
        )
        bound = reciprocal_tail_bound(20.0, envelope)
        self.assertFalse(bound.source_envelope_certified)
        self.assertFalse(bound.analytically_usable_for_r9)
        self.assertIn("CONDITIONAL", bound.epistemic_status)

    def test_count_envelope_evaluation(self):
        envelope = ZeroCountEnvelope(1.0, 2.0, 3.0, 4.0, 10.0, "test", True)
        t = 10.0
        expected = t * math.log(t) + 2 * t + 3 * math.log(t) + 4
        self.assertAlmostEqual(zero_count_upper(t, envelope), expected)

    def test_domain_and_source_validation(self):
        envelope = ZeroCountEnvelope(1.0, 0.0, 0.0, 0.0, 10.0, "test", True)
        with self.assertRaises(ValueError):
            reciprocal_tail_bound(9.0, envelope)
        with self.assertRaises(ValueError):
            ZeroCountEnvelope(1.0, 0.0, 0.0, 0.0, 1.0, "test").validate()
        with self.assertRaises(ValueError):
            ZeroCountEnvelope(1.0, 0.0, 0.0, 0.0, 10.0, "").validate()


if __name__ == "__main__":
    unittest.main()
