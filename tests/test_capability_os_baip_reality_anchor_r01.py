import json
import unittest
from pathlib import Path

from omega_capability_os_t.pilot_preregistration import (
    QuebecPilotPreregistration,
    evaluate_preregistration,
)


class BAIPRealityAnchorR01Tests(unittest.TestCase):
    def load_candidate(self):
        path = Path("pilots/quebec/baip_learnverify_candidate.draft.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload, QuebecPilotPreregistration.from_dict(payload)

    def test_candidate_is_explicitly_pre_outcome(self):
        payload, protocol = self.load_candidate()
        self.assertFalse(payload["outcomes_observed"])
        self.assertFalse(protocol.acceptance_rate_is_success_gate)
        self.assertFalse(protocol.personalized_psychological_targeting)

    def test_candidate_cannot_freeze_before_real_context_decisions(self):
        _, protocol = self.load_candidate()
        receipt = evaluate_preregistration(protocol)
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("unresolved_placeholder", receipt.blockers)
        self.assertFalse(receipt.execution_eligible)
        self.assertIsNone(receipt.protocol_digest)

    def test_candidate_keeps_current_practice_and_non_ai_baselines(self):
        _, protocol = self.load_candidate()
        alternatives = " | ".join(protocol.alternatives).lower()
        self.assertIn("current", alternatives)
        self.assertIn("human-only", alternatives)
        self.assertIn("checklist", alternatives)

    def test_transfer_outcome_is_after_ai_withdrawal(self):
        _, protocol = self.load_candidate()
        self.assertIn("without ai", protocol.transfer_observable.lower())
        self.assertIn("unavailable", protocol.withdrawal_condition.lower())

    def test_authority_is_not_assumed(self):
        _, protocol = self.load_candidate()
        self.assertTrue(protocol.authority_status.startswith("NOT_AUTHORIZED"))


if __name__ == "__main__":
    unittest.main()
