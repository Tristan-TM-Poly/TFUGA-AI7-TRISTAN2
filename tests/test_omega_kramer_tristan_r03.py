from __future__ import annotations

import math
import random
import unittest
from fractions import Fraction

from scripts.omega_kramer_tristan import cofactor_adjugate, det_bareiss, transpose
from scripts.omega_kramer_tristan_r03 import (
    backend_complexity_atlas,
    berkowitz_packet,
    build_berkowitz_circuit,
    demo_packet,
    higher_adjugate_tower_audit,
    kronecker_rewrite_audit,
    mixed_determinant_derivative,
    mixed_discriminant,
    rank_one_update_audit,
    rootflow_characteristic_bridge,
    schur_rewrite_audit,
    sylvester_rewrite_audit,
)


class TestOmegaKramerTristanR03(unittest.TestCase):
    def test_berkowitz_characteristic_and_determinant_random_exact(self):
        rng = random.Random(20260811)
        for n in range(1, 7):
            compiled = build_berkowitz_circuit(n)
            for _ in range(12):
                a = [[rng.randint(-3, 3) for _ in range(n)] for _ in range(n)]
                result = compiled.evaluate(a)
                self.assertEqual(result["determinant"], det_bareiss(a))
                coeffs = result["characteristic_coefficients_descending"]
                for lam in (-2, -1, 0, 1, 3):
                    value = Fraction(0)
                    for coefficient in coeffs:
                        value = value * lam + coefficient
                    shifted = [
                        [Fraction(lam if i == j else 0) - Fraction(a[i][j]) for j in range(n)]
                        for i in range(n)
                    ]
                    self.assertEqual(value, det_bareiss(shifted))

    def test_reverse_ad_adjugate_matches_independent_cofactors(self):
        fixtures = [
            [[2, 1, 0], [1, 3, 1], [0, 1, 2]],
            [[1, 2, 3], [2, 4, 6], [0, 1, 1]],
            [[0, 1, 2, 0], [1, 0, 3, 1], [2, 1, 0, 4], [0, 2, 1, 1]],
        ]
        for a in fixtures:
            result = build_berkowitz_circuit(len(a)).evaluate(a)
            self.assertEqual(result["adjugate"], cofactor_adjugate(a))

    def test_berkowitz_packet_crosschecks(self):
        packet = berkowitz_packet([[3, 1, 2], [0, 4, 1], [2, -1, 5]])
        self.assertTrue(packet["determinant_exact"])
        self.assertTrue(packet["adjugate_exact"])
        self.assertTrue(packet["characteristic_probe_exact"])
        self.assertTrue(packet["oak"]["division_free"])

    def test_static_circuit_crossover_exists_by_eight(self):
        atlas = backend_complexity_atlas(8)
        crossover = atlas["first_n_berkowitz_operation_nodes_not_larger"]
        self.assertIsNotNone(crossover)
        self.assertLessEqual(crossover, 8)
        self.assertFalse("runtime" in atlas.get("metric_boundary", "").lower() and "no runtime" not in atlas["metric_boundary"].lower())
        row8 = atlas["rows"][-1]
        self.assertLess(row8["berkowitz_operation_nodes"], row8["subset_operation_nodes"])

    def test_first_mixed_derivative_is_cofactor_contraction(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        h = [[1, 2, 0], [0, -1, 1], [2, 0, 3]]
        adj = cofactor_adjugate(a)
        cofactor = transpose(adj)
        expected = sum(
            (cofactor[i][j] * h[i][j] for i in range(3) for j in range(3)),
            Fraction(0),
        )
        self.assertEqual(mixed_determinant_derivative(a, [h]), expected)

    def test_second_mixed_derivative_is_symmetric(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        h1 = [[1, 0, 0], [0, 0, 2], [0, 1, 0]]
        h2 = [[0, 1, 0], [1, 0, 0], [0, 0, -1]]
        self.assertEqual(
            mixed_determinant_derivative(a, [h1, h2]),
            mixed_determinant_derivative(a, [h2, h1]),
        )

    def test_mixed_discriminant_normalization(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        self.assertEqual(mixed_discriminant([a, a, a]), det_bareiss(a))

    def test_higher_adjugate_compound_duality_entire_tower(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        audit = higher_adjugate_tower_audit(a)
        self.assertTrue(audit["all_dualities_exact"])
        self.assertTrue(audit["first_nonzero_order_matches_nullity"])
        self.assertEqual(len(audit["orders"]), 4)

    def test_higher_tower_on_rank_deficiency(self):
        a = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
        audit = higher_adjugate_tower_audit(a)
        self.assertTrue(audit["all_dualities_exact"])
        self.assertEqual(audit["singularity_ladder"]["nullity"], 1)
        self.assertEqual(audit["singularity_ladder"]["first_nonzero_higher_cofactor_order"], 1)

    def test_rootflow_bridge_exact_and_ascending(self):
        a = [[0, 1], [-2, -3]]
        bridge = rootflow_characteristic_bridge(a)
        # det(lambda I-A) = lambda^2 + 3 lambda + 2.
        self.assertEqual(bridge["coefficients_ascending"], (Fraction(2), Fraction(3), Fraction(1)))
        self.assertTrue(bridge["probe_exact"])
        self.assertTrue(bridge["rootflow_ready"])

    def test_rank_one_update_identity_is_global_even_when_singular(self):
        singular = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
        audit = rank_one_update_audit(singular, [1, 0, 1], [2, -1, 1])
        self.assertTrue(audit.exact)
        self.assertTrue(audit.globally_valid)
        self.assertTrue(audit.ledger.guard_satisfied)

    def test_sylvester_dimension_reduction(self):
        u = [[1, 2], [0, 1], [2, -1]]
        v = [[1, 0, 1], [2, 1, 0]]
        audit = sylvester_rewrite_audit(u, v)
        self.assertTrue(audit.exact)
        self.assertTrue(audit.globally_valid)
        self.assertEqual(audit.residual, 0)

    def test_kronecker_factorization(self):
        audit = kronecker_rewrite_audit([[1, 2], [3, 5]], [[2, 1], [0, 3]])
        self.assertTrue(audit.exact)
        self.assertTrue(audit.globally_valid)

    def test_schur_guard_and_exact_rewrite(self):
        good = schur_rewrite_audit([[2, 1, 1], [1, 3, 0], [2, 0, 4]], 2)
        self.assertTrue(good.exact)
        self.assertTrue(good.ledger.guard_satisfied)
        self.assertFalse(good.globally_valid)

        refused = schur_rewrite_audit([[1, 2, 0], [2, 4, 1], [0, 1, 3]], 2)
        self.assertFalse(refused.ledger.guard_satisfied)
        self.assertIsNone(refused.rhs)
        self.assertIsNone(refused.residual)

    def test_demo_evidence_surface(self):
        packet = demo_packet()
        self.assertTrue(packet["berkowitz"]["determinant_exact"])
        self.assertTrue(packet["berkowitz"]["adjugate_exact"])
        self.assertTrue(packet["higher_adjugate_tower"]["all_dualities_exact"])
        self.assertTrue(packet["rootflow_bridge"]["probe_exact"])
        self.assertTrue(packet["mixed_symmetry_exact"])
        self.assertTrue(packet["singular_rank_one_update"].exact)
        self.assertTrue(packet["sylvester"].exact)
        self.assertTrue(packet["kronecker"].exact)
        self.assertTrue(packet["schur"].exact)


if __name__ == "__main__":
    unittest.main()
