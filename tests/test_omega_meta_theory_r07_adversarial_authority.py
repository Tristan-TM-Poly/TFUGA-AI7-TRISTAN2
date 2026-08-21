import unittest

from omega_generative_closure_t.adversarial_authority import (
    ChallengeAuthority,
    challenge_diversity,
    detect_repair_overfit,
)
from omega_generative_closure_t.core import Rule
from omega_generative_closure_t.cross_context import ProbeFamily


class MetaTheoryR07AdversarialAuthorityTests(unittest.TestCase):
    def test_independent_authority_and_diverse_frozen_challenges_pass(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("a_to_y", ["a"], ["y"]),
            Rule.make("a_to_z", ["a"], ["z"]),
        )
        report = detect_repair_overfit(
            {"a"},
            rules,
            (ProbeFamily.make("generated", ["x"]),),
            (
                ProbeFamily.make("frozen-1", ["y"]),
                ProbeFamily.make("frozen-2", ["z"]),
            ),
            ChallengeAuthority("generator-A", "verifier-B", "authority-C"),
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertTrue(report.authority_independent)
        self.assertTrue(report.frozen_challenge_pass)
        self.assertFalse(report.repair_overfit)
        self.assertEqual(report.diversity.oak_status, "PASS")

    def test_repair_overfit_detected_against_frozen_challenge(self):
        rules = (Rule.make("a_to_x", ["a"], ["x"]),)
        report = detect_repair_overfit(
            {"a"},
            rules,
            (ProbeFamily.make("generated", ["x"]),),
            (
                ProbeFamily.make("frozen-1", ["x", "y"]),
                ProbeFamily.make("frozen-2", ["z"]),
            ),
            ChallengeAuthority("generator-A", "verifier-B", "authority-C"),
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertTrue(report.generated_probe_pass)
        self.assertFalse(report.frozen_challenge_pass)
        self.assertTrue(report.repair_overfit)
        self.assertIn("repair_overfit_detected", report.blockers)
        self.assertIn("frozen_challenge_failure", report.blockers)

    def test_role_collapse_blocks_promotion(self):
        rules = (
            Rule.make("a_to_x", ["a"], ["x"]),
            Rule.make("a_to_y", ["a"], ["y"]),
            Rule.make("a_to_z", ["a"], ["z"]),
        )
        report = detect_repair_overfit(
            {"a"},
            rules,
            (ProbeFamily.make("generated", ["x"]),),
            (
                ProbeFamily.make("frozen-1", ["y"]),
                ProbeFamily.make("frozen-2", ["z"]),
            ),
            ChallengeAuthority("same", "same", "authority-C"),
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertFalse(report.authority_independent)
        self.assertIn("generator_verifier_challenge_authority_not_independent", report.blockers)

    def test_collapsed_challenge_family_holds(self):
        diversity = challenge_diversity(
            (
                ProbeFamily.make("one", ["x"]),
                ProbeFamily.make("two", ["x"]),
            )
        )
        self.assertEqual(diversity.oak_status, "HOLD")
        self.assertIn("duplicate_or_collapsed_challenge_families", diversity.blockers)
        self.assertIn("zero_pairwise_challenge_diversity", diversity.blockers)

    def test_missing_frozen_family_is_rejected(self):
        with self.assertRaises(ValueError):
            detect_repair_overfit(
                {"a"},
                (),
                (ProbeFamily.make("generated", ["a"]),),
                (),
                ChallengeAuthority("g", "v", "c"),
            )


if __name__ == "__main__":
    unittest.main()
