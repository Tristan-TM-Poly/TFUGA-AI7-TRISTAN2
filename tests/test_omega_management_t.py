import math
import unittest

from omega_management_t import (
    InterventionCandidate,
    ManagementSignal,
    ManagementState,
    absence_resilience,
    leadership_value,
    prioritize_interventions,
    proxy_gap,
)


class ManagementKernelTests(unittest.TestCase):
    def test_presence_proxy_is_not_leadership(self):
        presence = ManagementSignal("hours_visible", 10.0, outcome_relevance=0.1, confidence=0.9)
        outcome = ManagementSignal("verified_outcome", 1.0, outcome_relevance=1.0, confidence=0.9)
        self.assertGreater(proxy_gap(presence, outcome), 0.7)

    def test_absence_resilience(self):
        self.assertAlmostEqual(absence_resilience(92.0, 100.0), 0.92)

    def test_absence_resilience_rejects_invalid_baseline(self):
        with self.assertRaises(ValueError):
            absence_resilience(1.0, 0.0)

    def test_leadership_value_rewards_capability_and_autonomy(self):
        a = ManagementState(1, 1, 1, 1, 1, 1, 3, 1, 1)
        b = ManagementState(2, 3, 2, 2, 3, 1, 1, 1, 1)
        self.assertGreater(leadership_value(b), leadership_value(a))

    def test_non_finite_state_fails_closed(self):
        with self.assertRaises(ValueError):
            ManagementState(math.inf, 1, 1, 1, 1, 1, 1, 1, 1)

    def test_unauthorized_candidate_never_ranks(self):
        candidates = [
            InterventionCandidate("unauthorized", 100, 0, 0, 0, 1, 1, authorized=False),
            InterventionCandidate("bounded", 2, 1, 0.1, 0.1, 1, 0.9, authorized=True),
        ]
        self.assertEqual([c.candidate_id for c in prioritize_interventions(candidates)], ["bounded"])

    def test_hard_blocker_is_non_compensatory(self):
        candidate = InterventionCandidate(
            "blocked", 1_000_000, 0, 0, 0, 1, 1, authorized=True, hard_blockers=("permission",)
        )
        self.assertEqual(prioritize_interventions([candidate]), [])

    def test_tie_does_not_create_semantic_winner(self):
        # Stable lexical order is serialization determinism only, not evidence that A is better.
        a = InterventionCandidate("a", 2, 1, 1, 1, 1, 1, authorized=True)
        b = InterventionCandidate("b", 2, 1, 1, 1, 1, 1, authorized=True)
        self.assertEqual([c.candidate_id for c in prioritize_interventions([b, a])], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
