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

import science_domain_oak_benchmark_suite as suite


class ScienceDomainOAKBenchmarkSuiteTests(unittest.TestCase):
    def test_science_oak_suite_runs_and_scores_benchmarks(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = suite.REPORT_PATH
            try:
                suite.REPORT_PATH = Path(tmp) / "science_oak_benchmark_report.json"
                report = suite.main(["--permutation-checks", "2"])
                self.assertIn("summary", report)
                self.assertGreaterEqual(report["summary"]["benchmark_count"], 8)
                self.assertTrue(suite.REPORT_PATH.exists())
                saved = json.loads(suite.REPORT_PATH.read_text(encoding="utf-8"))
                self.assertIn("results", saved)
                for result in saved["results"]:
                    self.assertIn(result["verdict"], {"CANON", "FERTILE", "M_MINUS"})
                    self.assertGreaterEqual(result["oak_score"], 0.0)
                    self.assertLessEqual(result["oak_score"], 100.0)
                    self.assertIn("truth", result)
                    self.assertIn("extracted", result)
                    self.assertIn("errors", result)
                    self.assertIn("jkd_verdict", result)
            finally:
                suite.REPORT_PATH = original

    def test_core_micro_oracles_are_canon_or_fertile(self):
        results = [suite.run_benchmark(bench, permutation_checks=1) for bench in suite.make_benchmarks()]
        by_name = {r.name: r for r in results}
        for name in [
            "physics_oscillator_frequency",
            "chemistry_three_peaks",
            "earth_diffusion_width",
            "life_genomic_motif_period",
            "epidemiology_logistic_midpoint",
        ]:
            self.assertIn(by_name[name].verdict, {"CANON", "FERTILE"}, name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
