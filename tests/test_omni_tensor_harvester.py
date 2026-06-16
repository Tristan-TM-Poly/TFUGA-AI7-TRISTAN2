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

import omni_tensor_harvester as omni


class OmniTensorHarvesterTests(unittest.TestCase):
    def test_offline_harvest_writes_accumulative_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = omni.REPORT_PATH
            try:
                omni.REPORT_PATH = Path(tmp) / "omni_harvester_report.json"
                run = omni.main(["--permutation-checks", "4"])
                self.assertIn("axes", run)
                self.assertEqual(set(run["axes"].keys()), {"finance_btc", "weather_wind", "nlp_wikipedia", "biology_dna", "cyber_traffic"})
                for payload in run["axes"].values():
                    self.assertIn("source", payload)
                    self.assertIn("strike", payload)
                    self.assertIn(payload["strike"]["verdict"], {"CANON", "FERTILE", "M_MINUS"})
                    self.assertGreaterEqual(payload["strike"]["oak_score"], 0.0)
                    self.assertLessEqual(payload["strike"]["oak_score"], 100.0)
                    self.assertIn("selected_invariants", payload["strike"])
                saved = json.loads(omni.REPORT_PATH.read_text(encoding="utf-8"))
                self.assertIn("runs", saved)
                self.assertEqual(len(saved["runs"]), 1)
                self.assertIn("last_run", saved)
            finally:
                omni.REPORT_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
