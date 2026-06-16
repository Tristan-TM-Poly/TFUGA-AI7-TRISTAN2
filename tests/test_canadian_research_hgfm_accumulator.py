#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

import canadian_research_hgfm_accumulator as hgfm


class CanadianResearchHGFMAccumulatorTests(unittest.TestCase):
    def test_canadian_research_hgfm_builds_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original = (hgfm.CANADA_REPORT, hgfm.OUT_DIR, hgfm.OUT_JSON, hgfm.OUT_MD, hgfm.OUT_M_MINUS)
            try:
                source = tmp_path / "canadian_university_research_report.json"
                out = tmp_path / "hgfm"
                source.write_text(json.dumps({
                    "runs": [{
                        "institutions": {
                            "Université de Montréal": {
                                "seed": {"province": "QC", "region": "Quebec", "priority": "P0"},
                                "source": "offline:test",
                                "works": [{"topic": "ai"}, {"topic": "health"}],
                                "strike": {"verdict": "FERTILE", "oak_score": 70.0, "selected_invariants": {"fractal_ratio": 0.2, "ffwt_energy_entropy": 0.4, "ffwt_mean_adjacent_coherence": 0.5, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.7, "null_z_score": 1.1, "null_percentile": 0.8}}
                            },
                            "McGill University": {
                                "seed": {"province": "QC", "region": "Quebec", "priority": "P0"},
                                "source": "offline:test",
                                "works": [{"topic": "ai"}, {"topic": "materials"}],
                                "strike": {"verdict": "FERTILE", "oak_score": 72.0, "selected_invariants": {"fractal_ratio": 0.21, "ffwt_energy_entropy": 0.41, "ffwt_mean_adjacent_coherence": 0.49, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.69, "null_z_score": 1.0, "null_percentile": 0.79}}
                            },
                            "University of Toronto": {
                                "seed": {"province": "ON", "region": "Canada", "priority": "P0"},
                                "source": "offline:test",
                                "works": [{"topic": "quantum"}],
                                "strike": {"verdict": "M_MINUS", "oak_score": 10.0, "selected_invariants": {"fractal_ratio": 0.01, "ffwt_energy_entropy": 0.95, "ffwt_mean_adjacent_coherence": 0.02, "ffwt_dominant_level": 1, "ffwt_dominant_relative_energy": 0.05, "null_z_score": -0.1, "null_percentile": 0.1}}
                            }
                        }
                    }]
                }), encoding="utf-8")
                hgfm.CANADA_REPORT = source
                hgfm.OUT_DIR = out
                hgfm.OUT_JSON = out / "canadian_research_hgfm_report.json"
                hgfm.OUT_MD = out / "CANADIAN_RESEARCH_HGFM_REPORT.md"
                hgfm.OUT_M_MINUS = out / "canadian_research_m_minus_compact.json"
                report = hgfm.main(["--threshold", "0.5"])
                self.assertEqual(report["summary"]["node_count"], 3)
                self.assertTrue(hgfm.OUT_JSON.exists())
                self.assertTrue(hgfm.OUT_MD.exists())
                self.assertTrue(hgfm.OUT_M_MINUS.exists())
                compact = json.loads(hgfm.OUT_M_MINUS.read_text(encoding="utf-8"))
                self.assertEqual(compact["count"], 1)
            finally:
                hgfm.CANADA_REPORT, hgfm.OUT_DIR, hgfm.OUT_JSON, hgfm.OUT_MD, hgfm.OUT_M_MINUS = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
