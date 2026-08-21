import unittest

from omega_generative_closure_t.adversarial_authority import ChallengeAuthority
from omega_generative_closure_t.causal_challenge import FrozenEvaluator
from omega_generative_closure_t.core import Rule
from omega_generative_closure_t.cross_context import ProbeFamily
from omega_generative_closure_t.shift_calibration import (
    adaptive_information_stop,
    calibrate_information_proxy,
    candidate_population_shift,
    challenge_family_ablation,
)


class MetaTheoryR09ShiftCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("b_to_y", ["b"], ["y"]),
            Rule.make("c_to_z", ["c"], ["z"]),
        )
        self.authority = ChallengeAuthority("generator", "verifier", "challenge-authority")
        self.evaluator = FrozenEvaluator("external-evaluator", "retained-ratio-v1", 1.0)

    def test_population_shift_holds_when_overlap_collapses(self):
        report = candidate_population_shift(
            ["A", "B", "C"], ["C", "D", "E"], min_jaccard_overlap=0.5
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("candidate_population_shift_exceeds_declared_tolerance", report.blockers)
        self.assertEqual(report.introduced, frozenset({"D", "E"}))

    def test_proxy_calibration_passes_small_error_and_holds_large_error(self):
        good = calibrate_information_proxy(
            [(1.0, 0.9), (0.5, 0.55), (0.2, 0.25)], max_mean_absolute_error=0.1
        )
        self.assertEqual(good.oak_status, "PASS")
        bad = calibrate_information_proxy(
            [(1.0, 0.0), (1.0, 0.1), (0.9, 0.0)], max_mean_absolute_error=0.2
        )
        self.assertEqual(bad.oak_status, "HOLD")
        self.assertIn("information_proxy_miscalibrated", bad.blockers)

    def test_challenge_ablation_finds_essential_family(self):
        report = challenge_family_ablation(
            {
                "A": {"a", "b"},
                "B": {"a"},
                "C": {"a", "b", "c"},
            },
            self.rules,
            (
                ProbeFamily.make("x", ["x"]),
                ProbeFamily.make("xy", ["x", "y"]),
                ProbeFamily.make("xyz", ["x", "y", "z"]),
            ),
            self.evaluator,
            self.authority,
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertGreaterEqual(report.baseline_distinct_signatures, 2)
        self.assertTrue(report.essential_families)

    def test_adaptive_stop_and_continue_are_explicit(self):
        stop = adaptive_information_stop([0.2, 0.03, 0.02, 0.01], window=3, min_mean_gain=0.05)
        self.assertEqual(stop.oak_status, "PASS")
        self.assertEqual(stop.decision, "STOP")
        cont = adaptive_information_stop([0.1, 0.08, 0.07], window=3, min_mean_gain=0.05)
        self.assertEqual(cont.decision, "CONTINUE")

    def test_insufficient_stop_history_holds(self):
        report = adaptive_information_stop([0.01], window=3)
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("insufficient_gain_history", report.blockers)


if __name__ == "__main__":
    unittest.main()
