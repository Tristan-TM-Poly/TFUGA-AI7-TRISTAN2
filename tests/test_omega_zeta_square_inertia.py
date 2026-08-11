from fractions import Fraction
import unittest

from omega_zeta_square_t.adversary import (
    finite_atomic_inertia_certificate,
    finite_atomic_inverse_moments,
)
from omega_zeta_square_t.certificates import exact_determinant, exact_hankel_matrix, exact_psd_report


class TestFiniteAtomicInertia(unittest.TestCase):
    def test_one_pair_has_one_negative_direction(self):
        cert = finite_atomic_inertia_certificate(3, 1)
        self.assertEqual(cert.support_size, 5)
        self.assertEqual(cert.positive_directions, 4)
        self.assertEqual(cert.negative_directions, 1)
        self.assertEqual(cert.zero_directions, 0)
        self.assertEqual(cert.determinant_sign, -1)
        self.assertFalse(cert.proves_rh)

    def test_two_pairs_have_two_negative_directions_and_positive_det_sign(self):
        cert = finite_atomic_inertia_certificate(1, 2)
        self.assertEqual(cert.support_size, 5)
        self.assertEqual((cert.positive_directions, cert.negative_directions), (3, 2))
        self.assertEqual(cert.determinant_sign, 1)

        moments = finite_atomic_inverse_moments(
            [Fraction(5)],
            [(Fraction(1), Fraction(1)), (Fraction(2), Fraction(1))],
            max_k=10,
        )
        full = exact_hankel_matrix(moments, size=5, shift=0)
        self.assertGreater(exact_determinant(full), 0)
        self.assertFalse(exact_psd_report(full).all_principal_minors_nonnegative)

    def test_no_complex_pairs_is_positive_inertia_metadata(self):
        cert = finite_atomic_inertia_certificate(4, 0)
        self.assertEqual((cert.positive_directions, cert.negative_directions), (4, 0))
        self.assertEqual(cert.determinant_sign, 1)

    def test_invalid_counts_rejected(self):
        with self.assertRaises(ValueError):
            finite_atomic_inertia_certificate(-1, 1)
        with self.assertRaises(ValueError):
            finite_atomic_inertia_certificate(1, -1)


if __name__ == "__main__":
    unittest.main()
