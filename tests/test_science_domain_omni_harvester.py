#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "core", ROOT / "prototypes"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import science_domain_omni_harvester as science


class ScienceDomainOmniHarvesterTests(unittest.TestCase):
    def test_science_domain_harvester_covers_major_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = science.REPORT_PATH
            try:
                science.REPORT_PATH = Path(tmp) / "science_domain_omni_report.json"
                run = science.main(["--permutation-checks", "3"])
                self.assertGreaterEqual(run["domain_count"], 30)
                families = {payload["family"] for payload in run["domains"].values()}
                self.assertTrue({"formal", "physical", "earth", "life", "cognitive_social", "engineering"}.issubset(families))
                for name, payload in run["domains"].items():
                    self.assertIn("strike", payload, name)
                    strike = payload["strike"]
                    self.assertIn(strike["verdict"], {"CANON", "FERTILE", "M_MINUS"}, name)
                    self.assertGreaterEqual(strike["oak_score"], 0.0, name)
                    self.assertLessEqual(strike["oak_score"], 100.0, name)
                    self.assertEqual(strike["flattened_size"], 512, name)
                    self.assertIn("selected_invariants", strike, name)
                saved = json.loads(science.REPORT_PATH.read_text(encoding="utf-8"))
                self.assertIn("runs", saved)
                self.assertEqual(saved["last_run"]["domain_count"], run["domain_count"])
            finally:
                science.REPORT_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
