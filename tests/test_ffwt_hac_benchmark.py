from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "prototypes" / "omega_ffwt_hac_cvcd"
if str(PROTO) not in sys.path:
    sys.path.insert(0, str(PROTO))

import run_ffwt_hac_benchmark as bench  # noqa: E402


class FFWTBenchmarkTest(unittest.TestCase):
    def test_feature_extractors_have_nonempty_vectors(self) -> None:
        sample = bench.make_synthetic_dataset(n_per_class=2, noise=0.0)[0]
        for feature_set in ["FFT", "DWT", "FFWT_HAC", "FFWT_PLUS_FFT"]:
            vector = bench.features(sample.signal, feature_set)
            self.assertGreater(len(vector), 0)
            self.assertTrue(all(isinstance(value, float) for value in vector))

    def test_benchmark_report_contains_required_oak_sections(self) -> None:
        report = bench.build_report([0.0], include_fixture=True)
        payload = bench.asdict(report)
        self.assertIn("synthetic", payload["datasets"])
        self.assertIn("csv_adapter_fixture", payload["datasets"])
        self.assertTrue(payload["classification_results"])
        self.assertTrue(payload["compression_results"])
        self.assertTrue(payload["winners_by_dataset_noise"])
        self.assertTrue(payload["ablation_summary"])
        self.assertIn("No general superiority", payload["oak_boundary"])
        self.assertTrue(any("Synthetic" in item for item in payload["m_minus"]))

    def test_csv_loader_accepts_values_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "signals.csv"
            csv_path.write_text("label,values\na,1 2 3 4\nb,4 3 2 1\n", encoding="utf-8")
            rows = bench.load_csv_dataset(csv_path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].label, "a")
            self.assertEqual(rows[0].source, "csv")

    def test_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "benchmark.json"
            out_md = Path(tmpdir) / "benchmark.md"
            subprocess.run(
                [
                    sys.executable,
                    str(PROTO / "run_ffwt_hac_benchmark.py"),
                    "--noise-levels",
                    "0.0",
                    "--output",
                    str(out_json),
                    "--markdown-output",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "ffwt-hac-cvcd-benchmark-v0.1")
            self.assertIn("M-minus", out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
