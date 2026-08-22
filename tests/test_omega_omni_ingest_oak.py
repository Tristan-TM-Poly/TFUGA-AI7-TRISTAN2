import tempfile
import unittest
from pathlib import Path

import omega_omni_ingest_oak as omni


class OmegaOmniIngestOakTests(unittest.TestCase):
    def test_source_capture_is_not_measurement(self):
        self.assertEqual(omni.verdict_for_capture(has_source=True).status.value, "SOURCE_CAPTURED")

    def test_test_receipt_is_software_only(self):
        self.assertEqual(
            omni.verdict_for_capture(has_source=True, has_test=True).status.value,
            "TESTED_SOFTWARE",
        )

    def test_automation_cannot_self_certify_measurement(self):
        with self.assertRaises(AssertionError):
            omni.assert_no_false_certification(omni.EvidenceStatus.MEASURED, automation_generated=True)

    def test_ssrf_private_ip_block(self):
        with self.assertRaises(omni.PolicyError):
            omni.NetworkPolicy().validate_url("https://127.0.0.1/private")

    def test_unknown_parser_stays_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sample = root / "sample.xyzlegacy"
            sample.write_bytes(b"a,b,c\n1,2,3\n")
            proposal = omni.propose_parser(sample, root / "proposals")
            self.assertEqual(proposal.status, "QUARANTINE")


if __name__ == "__main__":
    unittest.main()
