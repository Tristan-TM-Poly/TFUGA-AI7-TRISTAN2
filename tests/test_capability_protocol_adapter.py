import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CapabilityProtocolAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = json.loads((ROOT / "capability.json").read_text(encoding="utf-8"))

    def test_identity_and_protocol(self):
        self.assertEqual(self.adapter["id"], "tristan://repo/tfuga-ai7-tristan2")
        self.assertEqual(self.adapter["protocol"], "OMEGA-CAPABILITY-PROTOCOL-0")
        self.assertEqual(self.adapter["canonical_protocol"]["dependency_pr"], 609)
        self.assertTrue((ROOT / self.adapter["book0"]).exists())

    def test_public_capability_does_not_grant_repository_authority(self):
        authority = self.adapter["authority"]
        self.assertTrue(authority["read"])
        self.assertTrue(authority["inspect"])
        self.assertTrue(authority["run_sandbox"])
        for key in ("write", "merge", "deploy", "publish", "delete", "spend", "contact_third_party"):
            self.assertFalse(authority[key], key)

    def test_required_invariants_are_explicit(self):
        invariants = set(self.adapter["invariants"])
        self.assertIn("Capability != Authority", invariants)
        self.assertIn("Executable != Verified", invariants)
        self.assertIn("Composition != Validation", invariants)
        self.assertIn("SelfProposal != SelfApproval", invariants)

    def test_adapter_does_not_overclaim_repo_validation(self):
        self.assertEqual(self.adapter["evidence"]["status"], "IMPLEMENTED")
        self.assertIn("does not certify every", self.adapter["evidence"]["scope"])


if __name__ == "__main__":
    unittest.main()
