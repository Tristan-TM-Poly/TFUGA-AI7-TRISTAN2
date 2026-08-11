from __future__ import annotations

import unittest
from fractions import Fraction

from scripts.omega_kramer_tristan import det_bareiss
from scripts.omega_kramer_tristan_r04 import (
    _mv_mul,
    _mv_normalize,
    benchmark_matrix,
    bounded_rewrite_portfolio,
    characteristic_parameter_derivative,
    dm_inspired_decomposition,
    instrumented_bareiss,
    min_fill_width_heuristic,
    mode_velocity_packet,
    multivariate_guarded_cancel,
    oakbench_atlas,
    rank_k_update_polynomial,
)


class KramerR04Tests(unittest.TestCase):
    def test_instrumented_bareiss_matches_oracle(self) -> None:
        a = [[2, 1, 3], [1, 4, 2], [5, 0, 1]]
        packet = instrumented_bareiss(a)
        self.assertEqual(packet["determinant"], det_bareiss(a))
        self.assertGreaterEqual(packet["max_intermediate_bits"], 1)

    def test_benchmark_exactness_not_timing_order(self) -> None:
        packet = benchmark_matrix([[2, 1], [1, 3]], repeats=1)
        self.assertTrue(packet["all_exact"])
        self.assertFalse(packet["oak"]["timing_order_claimed"])
        self.assertIn("median_ns", packet["bareiss"]["observation"])

    def test_oakbench_all_families_exact(self) -> None:
        packet = oakbench_atlas(repeats=1)
        self.assertTrue(packet["all_exact"])
        self.assertGreaterEqual(len(packet["families"]), 5)

    def test_dm_inspired_partition_covers_rectangular_vertices(self) -> None:
        a = [[1, 0], [0, 1], [0, 1]]
        packet = dm_inspired_decomposition(a)
        self.assertEqual(packet["structural_rank"], 2)
        self.assertEqual(len(packet["unmatched_rows"]), 1)
        self.assertTrue(packet["vertex_cover_exact"])

    def test_structural_rank_not_exact_rank(self) -> None:
        a = [[1, 1], [1, 1]]
        packet = dm_inspired_decomposition(a)
        self.assertEqual(packet["structural_rank"], 2)
        self.assertEqual(packet["exact_rank"], 1)

    def test_min_fill_diagonal_width_zero(self) -> None:
        packet = min_fill_width_heuristic([[2, 0, 0], [0, 3, 0], [0, 0, 5]])
        self.assertEqual(packet["elimination_width_upper_bound"], 0)
        self.assertEqual(packet["fill_edges_added"], 0)

    def test_multivariate_guarded_cancellation_preserves_factor(self) -> None:
        variables = ("x", "y")
        factor = _mv_normalize({(1, 0): 1, (0, 1): 1}, variables)
        reduced_num = _mv_normalize({(1, 0): 1, (0, 0): 1}, variables)
        reduced_den = _mv_normalize({(0, 1): 1, (0, 0): 1}, variables)
        numerator = _mv_mul(factor, reduced_num)
        denominator = _mv_mul(factor, reduced_den)
        packet = multivariate_guarded_cancel(
            numerator, denominator, factor, variables=variables
        )
        self.assertTrue(packet["exact"])
        self.assertTrue(packet["ledger"].preserved)
        self.assertTrue(packet["ledger"].exact_division)

    def test_multivariate_refuses_nonfactor(self) -> None:
        variables = ("x", "y")
        packet = multivariate_guarded_cancel(
            {(1, 0): 1, (0, 0): 1},
            {(0, 1): 1, (0, 0): 1},
            {(1, 0): 1, (0, 1): 1},
            variables=variables,
        )
        self.assertFalse(packet["exact"])
        self.assertFalse(packet["ledger"].exact_division)

    def test_rank_k_update_is_singular_safe_and_degree_bounded(self) -> None:
        a = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
        u = [[1, 0], [0, 1], [1, 1]]
        v = [[1, 2, 0], [0, -1, 1]]
        packet = rank_k_update_polynomial(a, u, v)
        self.assertTrue(packet["base_singular"])
        self.assertTrue(packet["degree_bound_exact"])
        self.assertTrue(packet["probe_exact"])
        self.assertLessEqual(packet["update_rank"], 2)

    def test_rank_one_update_polynomial_degree_at_most_one(self) -> None:
        a = [[1, 0, 0], [0, 0, 0], [0, 0, 2]]
        u = [[1], [2], [3]]
        v = [[4, -1, 2]]
        packet = rank_k_update_polynomial(a, u, v)
        self.assertLessEqual(packet["update_rank"], 1)
        self.assertTrue(packet["degree_bound_exact"])
        self.assertTrue(packet["probe_exact"])

    def test_characteristic_parameter_reverse_ad_matches_interpolation(self) -> None:
        a = [[2, 1, 0], [0, 3, 1], [0, 0, 5]]
        h = [[1, 0, 2], [0, -2, 0], [0, 0, 3]]
        packet = characteristic_parameter_derivative(a, h)
        self.assertTrue(packet["reverse_ad_crosscheck_exact"])
        self.assertEqual(packet["derivative_coefficients_descending"][0], 0)

    def test_mode_velocity_diagonal_fixture(self) -> None:
        a = [[2, 0, 0], [0, 3, 0], [0, 0, 5]]
        h = [[5, 0, 0], [0, -1, 0], [0, 0, 2]]
        packet = mode_velocity_packet(a, h, 2)
        self.assertTrue(packet["accepted"])
        self.assertEqual(packet["velocity_exact"], Fraction(5))
        self.assertTrue(packet["coefficient_derivative_exact"])

    def test_mode_velocity_refuses_nonroot(self) -> None:
        packet = mode_velocity_packet([[2, 0], [0, 3]], [[1, 0], [0, 1]], 4)
        self.assertFalse(packet["accepted"])
        self.assertNotEqual(packet["root_residual"], 0)

    def test_mode_velocity_refuses_repeated_root(self) -> None:
        packet = mode_velocity_packet([[2, 0], [0, 2]], [[1, 0], [0, -1]], 2)
        self.assertFalse(packet["accepted"])
        self.assertEqual(packet["dP_dlambda"], 0)

    def test_portfolio_selects_compact_diagonal_representation(self) -> None:
        packet = bounded_rewrite_portfolio([[2, 0, 0], [0, 3, 0], [0, 0, 5]])
        self.assertTrue(packet["cvcd_agreement_exact"])
        self.assertEqual(packet["selected"].name, "diagonal-product")
        self.assertEqual(packet["selected"].value, 30)

    def test_portfolio_block_candidate_agrees(self) -> None:
        a = [[2, 1, 0, 0], [1, 3, 0, 0], [0, 0, 4, 1], [0, 0, 1, 5]]
        packet = bounded_rewrite_portfolio(a)
        self.assertTrue(packet["cvcd_agreement_exact"])
        names = [candidate.name for candidate in packet["candidates"]]
        self.assertIn("support-block-product", names)


if __name__ == "__main__":
    unittest.main()
