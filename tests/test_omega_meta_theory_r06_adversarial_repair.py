import unittest

from omega_generative_closure_t.adversarial_repair import (
    counterexample_repair_cycle,
    minimal_counterexample_repair,
    synthesize_adversarial_probe,
)
from omega_generative_closure_t.core import Rule
from omega_generative_closure_t.cross_context import ProbeFamily, cross_context_regeneration


class MetaTheoryR06AdversarialRepairTests(unittest.TestCase):
    def setUp(self):
        self.rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("b_to_z", ["b"], ["z"]),
            Rule.make("z_to_goal", ["z"], ["goal"]),
        )
        self.families = (
            ProbeFamily.make("train", ["x"]),
            ProbeFamily.make("external", ["goal"]),
        )

    def test_adversarial_probe_is_synthesized_from_transfer_residuals(self):
        report = cross_context_regeneration(
            {"a", "b"}, self.rules, self.families, training_family="train"
        )
        probe = synthesize_adversarial_probe(report)
        self.assertEqual(probe.observables, frozenset({"goal"}))
        self.assertEqual(probe.source_families, ("external",))

    def test_minimal_repair_adds_only_one_needed_seed(self):
        report = minimal_counterexample_repair(
            {"a"}, {"b", "unused"}, self.rules, self.families
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.added_seeds, frozenset({"b"}))
        self.assertEqual(report.min_retained_ratio, 1.0)

    def test_repair_holds_when_declared_pool_cannot_close_residual(self):
        report = minimal_counterexample_repair(
            {"a"}, {"unused"}, self.rules, self.families
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("no_declared_repair_satisfies_probe_families", report.blockers)

    def test_repair_cycle_preserves_old_basis_and_absorbs_counterexample(self):
        cross = cross_context_regeneration(
            {"a", "b"}, self.rules, self.families, training_family="train"
        )
        cycle = counterexample_repair_cycle(
            cross, {"b", "unused"}, self.rules, self.families
        )
        self.assertEqual(cycle.oak_status, "PASS")
        self.assertTrue(cycle.regression_preserved)
        self.assertEqual(cycle.repair.added_seeds, frozenset({"b"}))
        self.assertEqual(cycle.adversarial_probe.observables, frozenset({"goal"}))

    def test_relaxed_threshold_is_explicit(self):
        families = (
            ProbeFamily.make("train", ["x"]),
            ProbeFamily.make("mixed", ["x", "goal"]),
        )
        report = minimal_counterexample_repair(
            {"a"}, set(), self.rules, families, min_transfer_ratio=0.5
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.added_seeds, frozenset())


if __name__ == "__main__":
    unittest.main()
