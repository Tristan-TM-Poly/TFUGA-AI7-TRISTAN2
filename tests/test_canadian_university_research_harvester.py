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

import canadian_university_research_harvester as canada


class CanadianUniversityResearchHarvesterTests(unittest.TestCase):
    def test_offline_canadian_research_harvester(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = canada.REPORT_PATH
            try:
                canada.REPORT_PATH = Path(tmp) / "canadian_university_research_report.json"
                run = canada.main(["--priority", "P0", "--works-per-institution", "3", "--permutation-checks", "2"])
                self.assertIn("summary", run)
                self.assertGreaterEqual(run["summary"]["institution_count"], 10)
                self.assertIn("QC", run["summary"]["province_counts"])
                self.assertFalse(run["live_requested"])
                for name, payload in run["institutions"].items():
                    self.assertIn("seed", payload, name)
                    self.assertIn("works", payload, name)
                    self.assertEqual(payload["work_count"], 3, name)
                    self.assertIn("strike", payload, name)
                    self.assertIn(payload["strike"]["verdict"], {"CANON", "FERTILE", "M_MINUS"}, name)
                    self.assertGreaterEqual(payload["strike"]["oak_score"], 0.0, name)
                    self.assertLessEqual(payload["strike"]["oak_score"], 100.0, name)
                saved = json.loads(canada.REPORT_PATH.read_text(encoding="utf-8"))
                self.assertIn("runs", saved)
                self.assertIn("last_run", saved)
                self.assertEqual(saved["last_run"]["summary"]["institution_count"], run["summary"]["institution_count"])
            finally:
                canada.REPORT_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
