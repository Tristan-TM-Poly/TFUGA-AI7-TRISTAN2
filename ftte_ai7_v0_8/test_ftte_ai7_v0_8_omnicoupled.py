import tempfile
import unittest
from pathlib import Path

from ftte_ai7_v0_8_omnicoupled import (
    candidate,
    claims_for_packet,
    evidence_gate,
    build_hgfm,
    run,
)

class TestFTTEAI7V08OmniCoupled(unittest.TestCase):
    def test_candidate_menger_depth1(self):
        c = candidate("cube3", "menger_sponge", 1)
        self.assertEqual(c.cells, 20)
        self.assertGreater(c.power, 0)

    def test_evidence_gate_blocks_physical_claims(self):
        gate = evidence_gate(claims_for_packet())
        self.assertFalse(gate["stable_canon_allowed"])
        self.assertGreaterEqual(len(gate["blocked_claims"]), 3)

    def test_hgfm_hyperedges(self):
        c = [candidate("cube3", "menger_sponge", 1)]
        hg = build_hgfm(c)
        self.assertEqual(hg["kind"], "HGFM-OmniCoupled-v0.8")
        self.assertGreaterEqual(len(hg["hyperedges"]), 7)

    def test_run_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            manifest = run(d, max_depth=1, max_candidates=8)
            self.assertEqual(manifest["status"], "succeeded")
            self.assertFalse(manifest["stable_canon_allowed"])
            self.assertTrue((Path(d) / "DCTPP_REPORT_v0_8.md").exists())
            self.assertTrue((Path(d) / "evidence_gate.json").exists())

if __name__ == "__main__":
    unittest.main()
