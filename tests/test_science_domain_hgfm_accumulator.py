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

import science_domain_hgfm_accumulator as hgfm


class ScienceDomainHGFMAccumulatorTests(unittest.TestCase):
    def test_science_hgfm_builds_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original = (hgfm.SCIENCE_REPORT, hgfm.OUT_DIR, hgfm.OUT_JSON, hgfm.OUT_MD, hgfm.OUT_M_MINUS)
            try:
                source = tmp_path / "science_domain_omni_report.json"
                out = tmp_path / "hgfm"
                source.write_text(json.dumps({
                    "system": "test",
                    "runs": [{
                        "timestamp": "2026-06-16T00:00:00Z",
                        "domains": {
                            "physics_mechanics": {
                                "family": "physical",
                                "strike": {"verdict": "FERTILE", "oak_score": 60.0, "selected_invariants": {"fractal_ratio": 0.2, "ffwt_energy_entropy": 0.3, "ffwt_mean_adjacent_coherence": 0.1, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.6, "null_z_score": 1.0, "null_percentile": 0.8}}
                            },
                            "chemistry_spectroscopy": {
                                "family": "physical",
                                "strike": {"verdict": "M_MINUS", "oak_score": 10.0, "selected_invariants": {"fractal_ratio": 0.1, "ffwt_energy_entropy": 0.9, "ffwt_mean_adjacent_coherence": 0.01, "ffwt_dominant_level": 1, "ffwt_dominant_relative_energy": 0.2, "null_z_score": 0.0, "null_percentile": 0.1}}
                            },
                            "biology_genomics": {
                                "family": "life",
                                "strike": {"verdict": "FERTILE", "oak_score": 70.0, "selected_invariants": {"fractal_ratio": 0.25, "ffwt_energy_entropy": 0.4, "ffwt_mean_adjacent_coherence": 0.1, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.5, "null_z_score": 1.2, "null_percentile": 0.85}}
                            }
                        }
                    }]
                }), encoding="utf-8")
                hgfm.SCIENCE_REPORT = source
                hgfm.OUT_DIR = out
                hgfm.OUT_JSON = out / "science_domain_hgfm_report.json"
                hgfm.OUT_MD = out / "SCIENCE_DOMAIN_HGFM_REPORT.md"
                hgfm.OUT_M_MINUS = out / "science_domain_m_minus_compact.json"
                report = hgfm.main(["--threshold", "0.1"])
                self.assertEqual(report["summary"]["node_count"], 3)
                self.assertTrue(hgfm.OUT_JSON.exists())
                self.assertTrue(hgfm.OUT_MD.exists())
                self.assertTrue(hgfm.OUT_M_MINUS.exists())
                compact = json.loads(hgfm.OUT_M_MINUS.read_text(encoding="utf-8"))
                self.assertEqual(compact["count"], 1)
            finally:
                hgfm.SCIENCE_REPORT, hgfm.OUT_DIR, hgfm.OUT_JSON, hgfm.OUT_MD, hgfm.OUT_M_MINUS = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
