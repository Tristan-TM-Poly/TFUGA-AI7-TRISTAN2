from fractions import Fraction
import unittest

from omega_zeta_square_t import (
    RationalInterval,
    interval_psd_report,
    interval_stieltjes_certificate,
    inverse_moment_intervals_from_xi_even_derivatives,
)


class TestRationalIntervals(unittest.TestCase):
    def test_point_interval_pipeline_recovers_exact_two_atom_moments(self):
        # Synthetic xi-even derivative data chosen so
        # Theta/Theta(0)=1+(13/36)u+(1/36)u^2.
        derivatives = [
            RationalInterval.point(1),
            RationalInterval.point(Fraction(13, 18)),
            RationalInterval.point(Fraction(2, 3)),
        ]
        p = inverse_moment_intervals_from_xi_even_derivatives(derivatives)
        self.assertEqual(p[0], RationalInterval.point(Fraction(13, 36)))
        self.assertEqual(p[1], RationalInterval.point(Fraction(97, 1296)))

    def test_interval_stieltjes_certificate_on_exact_two_atom_data(self):
        l1, l2 = Fraction(1, 4), Fraction(1, 9)
        p = [RationalInterval.point(l1**k + l2**k) for k in range(1, 5)]
        cert = interval_stieltjes_certificate(p, hankel_size=2)
        self.assertTrue(cert.certified_finite_positive)
        self.assertFalse(cert.certified_finite_violation)
        self.assertFalse(cert.unresolved)
        self.assertFalse(cert.proves_rh)

    def test_interval_psd_detects_certified_negative_principal_minor(self):
        p = RationalInterval.point
        matrix = [
            [p(0), p(0), p(-3)],
            [p(0), p(-3), p(-3)],
            [p(-3), p(-3), p(-3)],
        ]
        report = interval_psd_report(matrix)
        self.assertTrue(report.certified_not_psd)
        bad = [m for m in report.minors if m.sign == "CERTIFIED_NEGATIVE"]
        self.assertTrue(any(m.indices == (0, 2) for m in bad))

    def test_wide_enclosure_can_remain_unresolved_without_false_promotion(self):
        p = [
            RationalInterval(Fraction(1), Fraction(1)),
            RationalInterval(Fraction(0), Fraction(2)),
            RationalInterval(Fraction(0), Fraction(3)),
            RationalInterval(Fraction(0), Fraction(4)),
        ]
        cert = interval_stieltjes_certificate(p, hankel_size=2)
        self.assertFalse(cert.certified_finite_positive)
        self.assertFalse(cert.proves_rh)

    def test_division_by_interval_containing_zero_is_rejected(self):
        with self.assertRaises(ZeroDivisionError):
            _ = RationalInterval.point(1) / RationalInterval(Fraction(-1), Fraction(1))


if __name__ == "__main__":
    unittest.main()
