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

import transversal_invariant_miner as tim


class TransversalInvariantMinerTests(unittest.TestCase):
    def test_tim_mines_candidates_from_synthetic_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original = (
                tim.SCIENCE_HGFM,
                tim.SCIENCE_OAK,
                tim.GENERAL_M_MINUS,
                tim.OUT_DIR,
                tim.OUT_JSON,
                tim.OUT_MD,
                tim.OUT_M_MINUS,
            )
            try:
                science_hgfm = tmp_path / "science_domain_hgfm_report.json"
                science_oak = tmp_path / "science_oak_benchmark_report.json"
                general_m_minus = tmp_path / "hgfm_m_minus_compact.json"
                out = tmp_path / "transversal"

                science_hgfm.write_text(json.dumps({
                    "nodes": [
                        {"id": "science:physics", "family": "physical", "domain": "physics_mechanics", "verdict": "FERTILE", "invariants": {"fractal_ratio": 0.2, "ffwt_energy_entropy": 0.4, "ffwt_mean_adjacent_coherence": 0.8, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.7, "null_z_score": 1.3, "null_percentile": 0.9}},
                        {"id": "science:neuro", "family": "life", "domain": "neuroscience_eeg", "verdict": "FERTILE", "invariants": {"fractal_ratio": 0.21, "ffwt_energy_entropy": 0.42, "ffwt_mean_adjacent_coherence": 0.79, "ffwt_dominant_level": 2, "ffwt_dominant_relative_energy": 0.69, "null_z_score": 1.31, "null_percentile": 0.88}},
                        {"id": "science:noise", "family": "formal", "domain": "statistics_probability", "verdict": "M_MINUS", "invariants": {"fractal_ratio": 0.01, "ffwt_energy_entropy": 0.95, "ffwt_mean_adjacent_coherence": 0.02, "ffwt_dominant_level": 1, "ffwt_dominant_relative_energy": 0.05, "null_z_score": -0.2, "null_percentile": 0.1}}
                    ]
                }), encoding="utf-8")

                science_oak.write_text(json.dumps({
                    "results": [
                        {"family": "physical", "verdict": "CANON", "oak_score": 90},
                        {"family": "life", "verdict": "FERTILE", "oak_score": 70},
                        {"family": "formal", "verdict": "M_MINUS", "oak_score": 20}
                    ]
                }), encoding="utf-8")
                general_m_minus.write_text(json.dumps({"count": 1, "nodes": []}), encoding="utf-8")

                tim.SCIENCE_HGFM = science_hgfm
                tim.SCIENCE_OAK = science_oak
                tim.GENERAL_M_MINUS = general_m_minus
                tim.OUT_DIR = out
                tim.OUT_JSON = out / "transversal_invariants.json"
                tim.OUT_MD = out / "TRANSVERSAL_INVARIANTS.md"
                tim.OUT_M_MINUS = out / "transversal_m_minus.json"

                report = tim.main(["--threshold", "0.90", "--max-candidates", "10"])
                self.assertIn("summary", report)
                self.assertGreaterEqual(report["summary"]["candidate_count"], 1)
                self.assertTrue(tim.OUT_JSON.exists())
                self.assertTrue(tim.OUT_MD.exists())
                self.assertTrue(tim.OUT_M_MINUS.exists())
                top = report["candidates"][0]
                self.assertIn("oak_next_test", top)
                self.assertIn("synthetic tensors are proxies", " ".join(top["risks"]))
                md = tim.OUT_MD.read_text(encoding="utf-8")
                self.assertIn("hypotheses", md)
                self.assertIn("not a proven scientific law", md)
            finally:
                (
                    tim.SCIENCE_HGFM,
                    tim.SCIENCE_OAK,
                    tim.GENERAL_M_MINUS,
                    tim.OUT_DIR,
                    tim.OUT_JSON,
                    tim.OUT_MD,
                    tim.OUT_M_MINUS,
                ) = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
