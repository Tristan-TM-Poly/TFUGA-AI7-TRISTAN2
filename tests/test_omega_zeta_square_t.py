import math
import unittest

from omega_zeta_square_t import (
    ClaimStatus,
    OakClaim,
    centered_square,
    decode_square,
    finite_stieltjes_report,
    in_centered_critical_strip,
    nontrivial_zero_image,
    rh_defect,
    strip_boundary,
    trivial_zero_image,
    validate_claim,
)
from omega_zeta_square_t.core import parabolic_tomography, parabolic_vertex_from_beta


class TestCenteredSquareGeometry(unittest.TestCase):
    def test_critical_line_maps_to_negative_real_axis(self):
        gamma = 14.134725141734693
        u = nontrivial_zero_image(0.5, gamma)
        self.assertAlmostEqual(u.imag, 0.0, places=12)
        self.assertLess(u.real, 0.0)
        self.assertAlmostEqual(u.real, -(gamma * gamma), places=10)
        self.assertAlmostEqual(rh_defect(u), 0.0, places=12)

    def test_exact_defect_recovers_horizontal_distance_squared(self):
        beta = 0.6
        gamma = 21.0
        u = nontrivial_zero_image(beta, gamma)
        decoded = decode_square(u)
        self.assertAlmostEqual(decoded.delta_squared, (beta - 0.5) ** 2, places=12)
        self.assertAlmostEqual(decoded.gamma_squared, gamma**2, places=10)

    def test_trivial_zero_images_are_positive_centered_squares(self):
        self.assertEqual(trivial_zero_image(1), 6.25)
        self.assertEqual(trivial_zero_image(2), 20.25)
        with self.assertRaises(ValueError):
            trivial_zero_image(0)

    def test_functional_pair_has_same_square_image(self):
        s = complex(0.37, 9.25)
        paired = 1.0 - s
        self.assertAlmostEqual(centered_square(s).real, centered_square(paired).real, places=12)
        self.assertAlmostEqual(centered_square(s).imag, centered_square(paired).imag, places=12)

    def test_strip_boundaries_collapse_to_same_parabola(self):
        for gamma in (0.0, 0.5, 2.0, 10.0):
            left = centered_square(complex(0.0, gamma))
            right = centered_square(complex(1.0, -gamma))
            self.assertAlmostEqual(left.real, right.real, places=12)
            self.assertAlmostEqual(left.imag, right.imag, places=12)
            self.assertAlmostEqual(left.real, strip_boundary(left.imag), places=12)
            self.assertTrue(in_centered_critical_strip(left))

    def test_tomography_stays_negative_on_rh(self):
        gamma = 14.0
        for b in (-10.0, 0.0, 14.0, 100.0):
            u = parabolic_tomography(0.5, gamma, b)
            self.assertAlmostEqual(u.imag, 0.0, places=12)
            self.assertLessEqual(u.real, 0.0)

    def test_off_line_tomography_vertex_is_defect(self):
        beta = 0.625
        gamma = 20.0
        u_vertex = parabolic_tomography(beta, gamma, gamma)
        expected = (beta - 0.5) ** 2
        self.assertAlmostEqual(u_vertex.real, expected, places=12)
        self.assertAlmostEqual(u_vertex.imag, 0.0, places=12)
        self.assertAlmostEqual(parabolic_vertex_from_beta(beta), expected, places=12)


class TestFiniteMomentDiagnostics(unittest.TestCase):
    def test_finite_atomic_measure_passes_hankel_checks(self):
        # First several known ordinates, used only as finite numerical sample data.
        gammas = [
            14.134725141734693,
            21.022039638771555,
            25.01085758014569,
            30.424876125859513,
            32.93506158773919,
            37.58617815882567,
        ]
        report = finite_stieltjes_report(gammas, hankel_size=2)
        self.assertTrue(report.finite_positive)
        self.assertFalse(report.proves_rh)
        self.assertEqual(report.epistemic_status, "NUMERICALLY_VERIFIED_FINITE_ONLY")
        self.assertEqual(report.gammas_checked, len(gammas))

    def test_invalid_gamma_rejected(self):
        with self.assertRaises(ValueError):
            finite_stieltjes_report([14.0, 0.0], hankel_size=2)


class TestOakGate(unittest.TestCase):
    def test_finite_numeric_rh_solution_claim_is_blocked(self):
        claim = OakClaim(
            statement="finite sample proves RH",
            status=ClaimStatus.NUMERICALLY_VERIFIED,
            finite_scope=True,
            claims_rh_solution=True,
        )
        verdict = validate_claim(claim)
        self.assertFalse(verdict.admissible)
        self.assertEqual(verdict.code, "BLOCK")

    def test_proof_with_conjectural_leaf_is_blocked(self):
        claim = OakClaim(
            statement="candidate proof",
            status=ClaimStatus.PROVED,
            dependencies=(ClaimStatus.KNOWN_THEOREM, ClaimStatus.CONJECTURE),
            claims_rh_solution=True,
        )
        self.assertFalse(validate_claim(claim).admissible)

    def test_proof_grade_dependencies_are_admissible_bookkeeping(self):
        claim = OakClaim(
            statement="local theorem assembled from proof-grade leaves",
            status=ClaimStatus.PROVED,
            dependencies=(ClaimStatus.KNOWN_THEOREM, ClaimStatus.PROVED),
        )
        self.assertTrue(validate_claim(claim).admissible)


if __name__ == "__main__":
    unittest.main()
