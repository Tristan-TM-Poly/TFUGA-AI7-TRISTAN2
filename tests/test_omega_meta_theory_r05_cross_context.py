import unittest

from omega_generative_closure_t.core import Rule
from omega_generative_closure_t.cross_context import (
    ProbeFamily,
    cross_context_regeneration,
    metric_sensitivity,
)


class MetaTheoryR05CrossContextTests(unittest.TestCase):
    def test_cross_context_pass_when_basis_transfers(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("x_to_y", ["x"], ["y"]),
        )
        report = cross_context_regeneration(
            {"a", "x"},
            rules,
            (
                ProbeFamily.make("train", ["x"]),
                ProbeFamily.make("transfer", ["y"]),
            ),
            training_family="train",
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertFalse(report.false_fixed_point)
        self.assertEqual(report.min_retained_ratio, 1.0)

    def test_false_fixed_point_detected_when_local_basis_fails_transfer(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("b_to_z", ["b"], ["z"]),
        )
        report = cross_context_regeneration(
            {"a", "b"},
            rules,
            (
                ProbeFamily.make("train", ["x"]),
                ProbeFamily.make("external", ["z"]),
            ),
            training_family="train",
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertTrue(report.false_fixed_point)
        self.assertIn("external", report.transfer_failures)
        self.assertIn("false_fixed_point_detected", report.blockers)

    def test_transfer_threshold_can_be_relaxed_explicitly(self):
        rules = (Rule.make("a_to_x", ["a"], ["x"]),)
        report = cross_context_regeneration(
            {"a"},
            rules,
            (
                ProbeFamily.make("train", ["x"]),
                ProbeFamily.make("mixed", ["x", "missing"]),
            ),
            training_family="train",
            min_transfer_ratio=0.5,
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.min_retained_ratio, 0.5)

    def test_metric_sensitivity_passes_only_on_same_winner(self):
        stable = metric_sensitivity({
            "accuracy": ["A", "B"],
            "cost": ["A", "C"],
        })
        self.assertEqual(stable.oak_status, "PASS")
        self.assertEqual(stable.stable_winner, "A")

        unstable = metric_sensitivity({
            "accuracy": ["A", "B"],
            "cost": ["B", "A"],
        })
        self.assertEqual(unstable.oak_status, "HOLD")
        self.assertIsNone(unstable.stable_winner)
        self.assertIn("metric_sensitive_winner", unstable.blockers)

    def test_metric_sensitivity_holds_without_evidence(self):
        report = metric_sensitivity({})
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("missing_metric_rankings", report.blockers)


if __name__ == "__main__":
    unittest.main()
