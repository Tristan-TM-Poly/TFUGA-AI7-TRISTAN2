import unittest

from omega_generative_closure_t.adversarial_authority import ChallengeAuthority
from omega_generative_closure_t.causal_challenge import (
    FrozenEvaluator,
    challenge_credit,
    evaluate_frozen_challenge,
    mutate_challenge_by_information_gain,
)
from omega_generative_closure_t.core import Rule
from omega_generative_closure_t.cross_context import ProbeFamily


class MetaTheoryR08CausalChallengeTests(unittest.TestCase):
    def setUp(self):
        self.rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("b_to_y", ["b"], ["y"]),
            Rule.make("c_to_z", ["c"], ["z"]),
        )
        self.authority = ChallengeAuthority("generator", "verifier", "challenge-authority")
        self.evaluator = FrozenEvaluator("external-evaluator", "retained-ratio-v1", 1.0)

    def test_challenge_credit_tracks_resolved_observables(self):
        credits = challenge_credit(
            {"a"},
            {"a", "b"},
            self.rules,
            (ProbeFamily.make("xy", ["x", "y"]),),
        )
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0].before_ratio, 0.5)
        self.assertEqual(credits[0].after_ratio, 1.0)
        self.assertEqual(credits[0].ratio_gain, 0.5)
        self.assertEqual(credits[0].resolved_observables, frozenset({"y"}))

    def test_frozen_evaluator_rejects_role_collapse(self):
        collapsed = ChallengeAuthority("generator", "verifier", "challenge-authority")
        report = evaluate_frozen_challenge(
            {"A": {"a"}},
            self.rules,
            ProbeFamily.make("x", ["x"]),
            FrozenEvaluator("generator", "criterion", 1.0),
            collapsed,
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("external_evaluator_role_collapsed", report.blockers)

    def test_information_gain_selects_unique_discriminating_mutation(self):
        decision = mutate_challenge_by_information_gain(
            ProbeFamily.make("seed", ["x"]),
            ["y", "z"],
            {
                "A": {"a", "b"},
                "B": {"a"},
                "C": {"a", "b"},
                "D": {"a"},
            },
            self.rules,
            self.evaluator,
            self.authority,
        )
        self.assertEqual(decision.oak_status, "PASS")
        self.assertIsNotNone(decision.selected)
        self.assertIn("y", decision.selected.observables)

    def test_information_gain_tie_remains_hold(self):
        decision = mutate_challenge_by_information_gain(
            ProbeFamily.make("seed", ["x"]),
            ["y", "z"],
            {
                "A": {"a", "b", "c"},
                "B": {"a"},
            },
            self.rules,
            self.evaluator,
            self.authority,
        )
        self.assertEqual(decision.oak_status, "HOLD")
        self.assertIsNone(decision.selected)
        self.assertIn("information_gain_tie_requires_additional_evidence", decision.blockers)

    def test_non_discriminating_mutations_hold(self):
        decision = mutate_challenge_by_information_gain(
            ProbeFamily.make("seed", ["x"]),
            ["y"],
            {
                "A": {"a", "b"},
                "B": {"a", "b"},
            },
            self.rules,
            self.evaluator,
            self.authority,
        )
        self.assertEqual(decision.oak_status, "HOLD")
        self.assertIn("no_discriminating_mutation", decision.blockers)


if __name__ == "__main__":
    unittest.main()
