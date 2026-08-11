from fractions import Fraction
import unittest

from omega_zeta_square_t import (
    ClaimStatus,
    OakClaim,
    centered_square,
    decode_square,
    finite_stieltjes_report,
    in_centered_critical_strip,
    inverse_moments_from_theta_coeffs,
    inverse_moments_from_xi_even_derivatives,
    nontrivial_zero_image,
    normalized_theta_coeffs_from_xi_even_derivatives,
    rh_defect,
    strip_boundary,
    trivial_zero_image,
    validate_claim,
    validate_proof_graph,
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


class TestFormalSeriesBridge(unittest.TestCase):
    def test_exact_two_atom_product_recovers_inverse_moments(self):
        # A(u)=(1+u/4)(1+u/9). Exact Fraction arithmetic avoids roundoff.
        a1 = Fraction(1, 4) + Fraction(1, 9)
        a2 = Fraction(1, 36)
        moments = inverse_moments_from_theta_coeffs([Fraction(1), a1, a2])
        self.assertEqual(moments[0], Fraction(1, 4) + Fraction(1, 9))
        self.assertEqual(moments[1], Fraction(1, 16) + Fraction(1, 81))

    def test_xi_even_derivative_normalization(self):
        # Synthetic derivatives chosen so normalized A(u)=1+u+u^2.
        derivs = [Fraction(2), Fraction(4), Fraction(48)]
        coeffs = normalized_theta_coeffs_from_xi_even_derivatives(derivs)
        self.assertEqual(coeffs, [Fraction(1), Fraction(1), Fraction(1)])
        moments = inverse_moments_from_xi_even_derivatives(derivs)
        self.assertEqual(moments, [Fraction(1), Fraction(-1)])


class TestProofGraphOak(unittest.TestCase):
    def test_valid_small_proof_graph(self):
        graph = {
            "nodes": [
                {"id": "a", "status": "KNOWN_THEOREM"},
                {"id": "b", "status": "PROVED"},
            ],
            "hyperedges": [
                {"id": "e", "sources": ["a"], "target": "b", "relation": "implies"}
            ],
        }
        self.assertEqual(validate_proof_graph(graph), [])

    def test_conjectural_leaf_cannot_feed_proved_target(self):
        graph = {
            "nodes": [
                {"id": "a", "status": "CONJECTURE"},
                {"id": "b", "status": "PROVED"},
            ],
            "hyperedges": [
                {"id": "e", "sources": ["a"], "target": "b", "relation": "implies"}
            ],
        }
        errors = validate_proof_graph(graph)
        self.assertEqual(len(errors), 1)
        self.assertIn("non-proof-grade", errors[0])


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
