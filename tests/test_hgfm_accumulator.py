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

import hgfm_accumulator as hgfm


class HGFMAccumulatorTests(unittest.TestCase):
    def test_accumulator_builds_reports_from_synthetic_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_paths = (
                hgfm.OMNI_REPORT,
                hgfm.JKD_REPORT,
                hgfm.OAK_REPORT,
                hgfm.OUT_DIR,
                hgfm.OUT_JSON,
                hgfm.OUT_MD,
                hgfm.OUT_M_MINUS,
            )
            try:
                reports = tmp_path / "reports"
                omni_path = reports / "jkd" / "omni_harvester_report.json"
                jkd_path = reports / "jkd" / "jkd_tensor_inputs_report.json"
                oak_path = tmp_path / "omega_max_oak_report.json"
                out_dir = reports / "hgfm"
                omni_path.parent.mkdir(parents=True)
                oak_path.parent.mkdir(parents=True, exist_ok=True)

                omni_path.write_text(json.dumps({
                    "system": "test",
                    "runs": [{
                        "timestamp": "2026-06-16T00:00:00Z",
                        "axes": {
                            "finance_btc": {
                                "source": "offline:test",
                                "metadata": {},
                                "strike": {
                                    "verdict": "FERTILE",
                                    "oak_score": 55.0,
                                    "selected_invariants": {
                                        "fractal_ratio": 0.2,
                                        "ffwt_energy_entropy": 0.4,
                                        "ffwt_mean_adjacent_coherence": 0.1,
                                        "ffwt_dominant_level": 3,
                                        "ffwt_dominant_relative_energy": 0.5,
                                        "null_z_score": 1.2,
                                        "null_percentile": 0.8
                                    }
                                }
                            },
                            "cyber_traffic": {
                                "source": "offline:test",
                                "metadata": {},
                                "strike": {
                                    "verdict": "M_MINUS",
                                    "oak_score": 20.0,
                                    "selected_invariants": {
                                        "fractal_ratio": 0.05,
                                        "ffwt_energy_entropy": 0.95,
                                        "ffwt_mean_adjacent_coherence": 0.02,
                                        "ffwt_dominant_level": 1,
                                        "ffwt_dominant_relative_energy": 0.1,
                                        "null_z_score": -0.1,
                                        "null_percentile": 0.2
                                    }
                                }
                            }
                        }
                    }]
                }), encoding="utf-8")

                jkd_path.write_text(json.dumps({"results": {}}), encoding="utf-8")
                oak_path.write_text(json.dumps({"results": [
                    {"benchmark": "B1", "verdict": "CANON", "oak_score": 93.0, "errors": {"e": 0.01}, "relation_type": "test"}
                ]}), encoding="utf-8")

                hgfm.OMNI_REPORT = omni_path
                hgfm.JKD_REPORT = jkd_path
                hgfm.OAK_REPORT = oak_path
                hgfm.OUT_DIR = out_dir
                hgfm.OUT_JSON = out_dir / "hgfm_accumulator_report.json"
                hgfm.OUT_MD = out_dir / "HGFM_ACCUMULATOR_REPORT.md"
                hgfm.OUT_M_MINUS = out_dir / "hgfm_m_minus_compact.json"

                report = hgfm.main(["--threshold", "0.1"])
                self.assertIn("summary", report)
                self.assertGreaterEqual(report["summary"]["node_count"], 3)
                self.assertTrue(hgfm.OUT_JSON.exists())
                self.assertTrue(hgfm.OUT_MD.exists())
                self.assertTrue(hgfm.OUT_M_MINUS.exists())
                compact = json.loads(hgfm.OUT_M_MINUS.read_text(encoding="utf-8"))
                self.assertEqual(compact["count"], 1)
            finally:
                (
                    hgfm.OMNI_REPORT,
                    hgfm.JKD_REPORT,
                    hgfm.OAK_REPORT,
                    hgfm.OUT_DIR,
                    hgfm.OUT_JSON,
                    hgfm.OUT_MD,
                    hgfm.OUT_M_MINUS,
                ) = original_paths


if __name__ == "__main__":
    unittest.main(verbosity=2)
