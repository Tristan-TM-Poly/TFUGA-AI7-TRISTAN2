from __future__ import annotations

import random
import unittest
from fractions import Fraction

from scripts.omega_kramer_tristan import cofactor_adjugate, det_bareiss, transpose
from scripts.omega_kramer_tristan_r02 import (
    build_determinant_circuit,
    deterministic_benchmark_atlas,
    directional_determinantal_jet,
    division_free_packet,
    generalized_cofactors,
    poly_eval,
    route_backend,
    simplify_rational_polynomials,
    singularity_ladder,
    structural_profile,
)


class OmegaKramerTristanR02Tests(unittest.TestCase):
    def test_division_free_circuit_matches_bareiss_and_adjugate(self):
        rng = random.Random(20260811)
        for n in range(1, 6):
            compiled = build_determinant_circuit(n)
            for _ in range(20):
                matrix = [[rng.randint(-3, 3) for _ in range(n)] for _ in range(n)]
                result = compiled.determinant_and_adjugate(matrix)
                self.assertEqual(result["determinant"], det_bareiss(matrix))
                self.assertEqual(result["adjugate"], cofactor_adjugate(matrix))

    def test_circuit_is_division_free_and_hash_consed(self):
        compiled = build_determinant_circuit(5)
        ops = {node.op for node in compiled.circuit.nodes}
        self.assertLessEqual(ops, {"const", "var", "add", "mul"})
        self.assertEqual(compiled.transitions, 5 * 2**4)
        metrics = compiled.circuit.metrics()
        self.assertEqual(metrics["nodes"], 184)
        self.assertLess(metrics["operation_nodes"], 5 * 5 * 24 + 120)

    def test_r02_crosschecks_r01_and_reports_boundary(self):
        matrix = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        packet = division_free_packet(matrix)
        self.assertTrue(packet["bareiss_exact"])
        self.assertTrue(packet["cofactor_crosscheck_exact"])
        self.assertTrue(packet["r01_subset_crosscheck_exact"])
        self.assertIn("not a runtime-speedup claim", packet["shared_metrics"]["metric_boundary"])

    def test_directional_determinantal_jet_is_exact(self):
        a = [[1, 2], [3, 4]]
        h = [[2, 0], [0, 1]]
        jet = directional_determinantal_jet(a, h)
        self.assertEqual(jet.coefficients, (Fraction(-2), Fraction(9), Fraction(2)))
        self.assertEqual(jet.derivatives_at_zero, (Fraction(-2), Fraction(9), Fraction(4)))
        self.assertEqual(jet.validation_residual, 0)
        for t in range(-3, 5):
            shifted = [[a[i][j] + t * h[i][j] for j in range(2)] for i in range(2)]
            self.assertEqual(poly_eval(jet.coefficients, t), det_bareiss(shifted))

    def test_generalized_order_one_is_cofactor_matrix(self):
        matrix = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        tensor = generalized_cofactors(matrix, 1)
        self.assertEqual(transpose(tensor["values"]), cofactor_adjugate(matrix))

    def test_generalized_endpoints(self):
        matrix = [[2, 1], [3, 4]]
        self.assertEqual(generalized_cofactors(matrix, 0)["values"], [[det_bareiss(matrix)]])
        self.assertEqual(generalized_cofactors(matrix, 2)["values"], [[Fraction(1)]])

    def test_singularity_ladder_matches_nullity(self):
        fixtures = [
            ([[1, 0, 0], [0, 2, 0], [0, 0, 3]], 0),
            ([[1, 2, 3], [2, 4, 6], [0, 1, 1]], 1),
            ([[1, 2, 3], [2, 4, 6], [3, 6, 9]], 2),
            ([[0, 0], [0, 0]], 2),
        ]
        for matrix, nullity in fixtures:
            packet = singularity_ladder(matrix)
            self.assertEqual(packet["nullity"], nullity)
            self.assertTrue(packet["rank_order_identity_exact"])
            self.assertEqual(packet["first_nonzero_higher_cofactor_order"], nullity)

    def test_domain_ledger_preserves_cancelled_factor(self):
        guarded = simplify_rational_polynomials([-2, 1, 1], [-3, 2, 1])
        self.assertEqual(guarded.numerator, (Fraction(2), Fraction(1)))
        self.assertEqual(guarded.denominator, (Fraction(3), Fraction(1)))
        self.assertEqual(guarded.ledger.cancelled_factor, (Fraction(-1), Fraction(1)))
        self.assertEqual(guarded.ledger.original_denominator, (Fraction(-3), Fraction(2), Fraction(1)))
        self.assertTrue(guarded.ledger.cancellation_preserved)

    def test_structural_profile_and_router_detect_blocks(self):
        matrix = [
            [2, 1, 0, 0],
            [1, 3, 0, 0],
            [0, 0, 4, 1],
            [0, 0, 1, 5],
        ]
        profile = structural_profile(matrix)
        self.assertEqual(profile["structural_rank"], 4)
        self.assertEqual(profile["exact_rank"], 4)
        self.assertEqual(len(profile["balanced_nonzero_blocks"]), 2)
        self.assertEqual(route_backend(matrix)["backend"], "block-decomposition")

    def test_router_blocks_cramer_division_on_exact_singularity(self):
        matrix = [[1, 1], [2, 2]]
        route = route_backend(matrix)
        self.assertEqual(route["backend"], "singularity-ladder")
        self.assertEqual(route["profile"]["exact_rank"], 1)
        self.assertEqual(route["profile"]["structural_rank"], 2)

    def test_benchmark_atlas_is_deterministic_and_claim_safe(self):
        atlas = deterministic_benchmark_atlas()
        self.assertFalse(atlas["timing_claimed"])
        self.assertEqual(atlas["families"]["diagonal6"]["route"], "diagonal-closed-form")
        self.assertEqual(atlas["families"]["block6"]["route"], "block-decomposition")
        self.assertEqual(atlas["families"]["rank_deficient4"]["route"], "singularity-ladder")
        self.assertEqual(atlas["families"]["vandermonde5"]["exact_rank"], 5)


if __name__ == "__main__":
    unittest.main()
