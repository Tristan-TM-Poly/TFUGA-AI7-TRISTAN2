import unittest

from omega_generative_closure_t.core import MaxMinVector, Rule
from omega_generative_closure_t.geometry import closure_gradient, pairwise_seed_curvature
from omega_generative_closure_t.maxmin import dominates
from omega_generative_closure_t.morphogenesis import (
    compile_residual_field,
    minimal_generating_basis,
    renormalize_seed_set,
)
from omega_generative_closure_t.theory_evolution import (
    power_ladder_step,
    regeneration_benchmark,
    select_next_transformation,
)


class MetaTheoryEvolutionR04Tests(unittest.TestCase):
    def test_r03_gradient_and_pairwise_curvature(self):
        rules = (Rule.make("joint", ("A", "B"), ("X",)),)
        gains = closure_gradient(("A",), rules, ("B", "C"))
        self.assertEqual(gains[0].candidate, "B")
        self.assertEqual(gains[0].derived_added, frozenset({"X"}))
        self.assertEqual(pairwise_seed_curvature((), rules, "A", "B").curvature, 1)

    def test_extended_axes_participate_in_pareto_dominance(self):
        stronger = MaxMinVector(
            verified_value=1.0,
            interoperability=1.0,
            synergy=1.0,
            transferability=1.0,
            risk=0.1,
        )
        weaker = MaxMinVector(verified_value=1.0, risk=0.2)
        self.assertTrue(dominates(stronger, weaker))

    def test_residual_field_and_minimal_basis(self):
        rules = (
            Rule.make("derive-x", ("A",), ("X",)),
            Rule.make("derive-y", ("X", "B"), ("Y",)),
        )
        field = compile_residual_field(("A",), rules, ("Y", "Z"))
        self.assertEqual(field.missing, frozenset({"Y", "Z"}))
        self.assertIn(("derive-y", ("B",)), field.blocked_rules)
        self.assertEqual(field.unproduced, frozenset({"Z"}))

        basis = minimal_generating_basis(("A", "B", "X"), rules, required=("Y",))
        self.assertTrue(frozenset({"Y"}) <= basis.reachable)
        self.assertLess(len(basis.basis), 3)

    def test_renormalization_is_second_pass_stable(self):
        rules = (Rule.make("derive-c", ("A",), ("C",)),)
        receipt = renormalize_seed_set(("A", "B", "C"), rules)
        self.assertFalse(receipt.lost_observables)
        self.assertTrue(receipt.stable_under_second_pass)

    def test_regeneration_benchmark_preserves_goal_and_ablation_exposes_loss(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"], cost=1.5, evidence=0.9),
            Rule.make("x_to_goal", ["x"], ["goal"], cost=2.0, evidence=0.8),
        )
        report = regeneration_benchmark({"a", "x"}, rules, observables={"goal"})
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.retained_observables_ratio, 1.0)
        self.assertEqual(len(report.reduced_seeds), 1)
        self.assertEqual(report.ablations[0].lost_observables, frozenset({"goal"}))

    def test_evidence_floor_can_hold_structural_regeneration(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"], evidence=0.9),
            Rule.make("x_to_goal", ["x"], ["goal"], evidence=0.8),
        )
        report = regeneration_benchmark(
            {"a"}, rules, observables={"goal"}, min_rule_evidence=0.95
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("fired_rule_evidence_below_declared_floor", report.blockers)

    def test_selection_has_identity_and_refuses_incomparable_tie(self):
        self.assertEqual(select_next_transformation({}).decision, "IDENTITY")

        evidence_heavy = MaxMinVector(verified_value=1.0, evidence=3.0, cost=2.0)
        cheap = MaxMinVector(verified_value=2.0, evidence=1.0, cost=1.0)
        tie = select_next_transformation({"evidence_heavy": evidence_heavy, "cheap": cheap})
        self.assertEqual(tie.decision, "HOLD")
        self.assertEqual(set(tie.pareto_frontier), {"evidence_heavy", "cheap"})

        weak = MaxMinVector(verified_value=1.0, evidence=1.0, cost=2.0)
        strong = MaxMinVector(verified_value=2.0, evidence=1.0, cost=1.0)
        selected = select_next_transformation({"weak": weak, "strong": strong})
        self.assertEqual(selected.decision, "strong")

    def test_2n_ladder_executes_n_plus_one_probe(self):
        step = power_ladder_step(3)
        self.assertEqual(step.current_capacity, 8)
        self.assertEqual(step.probe_n, 4)
        self.assertEqual(step.probe_capacity, 16)


if __name__ == "__main__":
    unittest.main()
