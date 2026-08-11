import random
import unittest
from fractions import Fraction

from scripts.omega_kramer_tristan import (
    bordered_identity_residual,
    cofactor_adjugate,
    compound_matrix,
    det_bareiss,
    determinant_adjugate_dag,
    identity,
    kramer_packet,
    matmul,
    multi_rhs_packet,
)


class OmegaKramerTristanTests(unittest.TestCase):
    def test_subset_dag_matches_bareiss_on_deterministic_random_matrices(self):
        rng = random.Random(20260811)
        for n in range(1, 7):
            for _ in range(20):
                a = [[rng.randint(-4, 4) for _ in range(n)] for _ in range(n)]
                self.assertEqual(determinant_adjugate_dag(a).determinant, det_bareiss(a))

    def test_reverse_ad_adjugate_matches_independent_cofactor_oracle(self):
        fixtures = [
            [[5]],
            [[2, 3], [7, 11]],
            [[2, 1, 0], [1, 3, 1], [0, 1, 2]],
            [[1, 2, 3], [2, 4, 6], [0, 1, 1]],
        ]
        for a in fixtures:
            dag = determinant_adjugate_dag(a)
            self.assertEqual([list(row) for row in dag.adjugate], cofactor_adjugate(a))

    def test_adjugate_identity_is_exact_even_for_singular_matrix(self):
        for a in (
            [[2, 1], [1, 3]],
            [[1, 2, 3], [2, 4, 6], [0, 1, 1]],
        ):
            dag = determinant_adjugate_dag(a)
            adj = [list(row) for row in dag.adjugate]
            lhs = matmul(a, adj)
            rhs = [[dag.determinant * x for x in row] for row in identity(len(a))]
            self.assertEqual(lhs, rhs)

    def test_kramer_packet_solves_and_certifies(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        b = [1, 2, 3]
        packet = kramer_packet(a, b)
        self.assertEqual(packet["determinant"], Fraction(8))
        self.assertEqual(packet["solution"], [Fraction(1, 2), Fraction(0), Fraction(3, 2)])
        self.assertTrue(packet["certificate_exact"])
        self.assertTrue(packet["crosscheck_exact"])
        self.assertEqual(packet["classification"]["classification"], "unique")

    def test_bordered_generator_identity(self):
        a = [[3, -1, 2], [0, 4, 1], [2, 1, 5]]
        b = [2, -3, 7]
        for z, alpha in (([1, 0, -2], 3), ([2, 5, 1], -4), ([0, 0, 0], 9)):
            self.assertEqual(bordered_identity_residual(a, b, z, alpha), 0)

    def test_singular_classification_preserves_no_division(self):
        consistent = kramer_packet([[1, 2], [2, 4]], [3, 6])
        inconsistent = kramer_packet([[1, 2], [2, 4]], [3, 7])
        self.assertEqual(consistent["classification"]["classification"], "infinitely_many")
        self.assertEqual(inconsistent["classification"]["classification"], "inconsistent")
        self.assertIsNone(consistent["solution"])
        self.assertIsNone(inconsistent["solution"])
        self.assertFalse(consistent["domain_ledger"]["division_performed"])
        self.assertTrue(consistent["certificate_exact"])

    def test_multi_rhs_reuses_one_adjugate(self):
        a = [[2, 1], [1, 3]]
        b = [[1, 4, 0], [2, -1, 5]]
        packet = multi_rhs_packet(a, b)
        self.assertEqual(packet["determinant"], 5)
        self.assertTrue(packet["certificate_exact"])
        self.assertEqual(
            packet["solutions"],
            [
                [Fraction(1, 5), Fraction(13, 5), Fraction(-1)],
                [Fraction(3, 5), Fraction(-6, 5), Fraction(2)],
            ],
        )

    def test_compound_matrix_extremes(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        c0 = compound_matrix(a, 0)
        c1 = compound_matrix(a, 1)
        c3 = compound_matrix(a, 3)
        self.assertEqual(c0["values"], [[1]])
        self.assertEqual(c1["values"], [[Fraction(x) for x in row] for row in a])
        self.assertEqual(c3["values"], [[det_bareiss(a)]])

    def test_dag_metrics_match_subset_lattice_counts(self):
        for n in range(1, 8):
            a = identity(n)
            metrics = determinant_adjugate_dag(a).metrics
            self.assertEqual(metrics.stored_states, 2**n)
            self.assertEqual(metrics.transitions, n * 2 ** (n - 1))
            self.assertEqual(metrics.leibniz_terms, math_factorial(n))


def math_factorial(n):
    out = 1
    for k in range(2, n + 1):
        out *= k
    return out


if __name__ == "__main__":
    unittest.main()
