import unittest

from omega_generative_closure_t.core import MaxMinVector, Rule
from omega_generative_closure_t.theory_evolution import (
    power_ladder_step,
    regeneration_benchmark,
    select_next_transformation,
)


class TheoryEvolutionR04Tests(unittest.TestCase):
    def setUp(self):
        self.rules = (
            Rule.make("a_to_x", ["a"], ["x"], cost=1.5, evidence=0.9),
            Rule.make("x_to_goal", ["x"], ["goal"], cost=2.0, evidence=0.8),
        )

    def test_regeneration_compresses_redundant_seed_and_preserves_goal(self):
        report = regeneration_benchmark(
            {"a", "x"},
            self.rules,
            observables={"goal"},
            min_rule_evidence=0.0,
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.retained_observables_ratio, 1.0)
        self.assertEqual(len(report.reduced_seeds), 1)
        self.assertGreater(report.compression_ratio, 0.0)
        self.assertTrue(report.stable_under_second_pass)

    def test_ablation_exposes_necessity_inside_selected_basis(self):
        report = regeneration_benchmark({"a", "x"}, self.rules, observables={"goal"})
        self.assertEqual(len(report.ablations), 1)
        self.assertEqual(report.ablations[0].lost_observables, frozenset({"goal"}))

    def test_evidence_floor_can_hold_structural_pass(self):
        report = regeneration_benchmark(
            {"a"},
            self.rules,
            observables={"goal"},
            min_rule_evidence=0.95,
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertGreater(report.evidence_debt, 0.0)
        self.assertIn("fired_rule_evidence_below_declared_floor", report.blockers)

    def test_unique_pareto_survivor_is_selected_without_scalarization(self):
        weak = MaxMinVector(verified_value=1.0, evidence=1.0, cost=2.0)
        strong = MaxMinVector(verified_value=2.0, evidence=1.0, cost=1.0)
        decision = select_next_transformation({"weak": weak, "strong": strong})
        self.assertEqual(decision.decision, "strong")
        self.assertEqual(decision.oak_status, "PASS")

    def test_incomparable_candidates_hold_instead_of_fabricating_winner(self):
        evidence_heavy = MaxMinVector(verified_value=1.0, evidence=3.0, cost=2.0)
        cheap = MaxMinVector(verified_value=2.0, evidence=1.0, cost=1.0)
        decision = select_next_transformation(
            {"evidence_heavy": evidence_heavy, "cheap": cheap}
        )
        self.assertEqual(decision.decision, "HOLD")
        self.assertEqual(decision.oak_status, "HOLD")
        self.assertEqual(set(decision.pareto_frontier), {"evidence_heavy", "cheap"})

    def test_no_candidate_means_identity(self):
        decision = select_next_transformation({})
        self.assertEqual(decision.decision, "IDENTITY")
        self.assertEqual(decision.oak_status, "PASS")

    def test_power_ladder_always_exposes_n_plus_one_probe(self):
        step = power_ladder_step(5)
        self.assertEqual(step.current_capacity, 32)
        self.assertEqual(step.probe_n, 6)
        self.assertEqual(step.probe_capacity, 64)


if __name__ == "__main__":
    unittest.main()
