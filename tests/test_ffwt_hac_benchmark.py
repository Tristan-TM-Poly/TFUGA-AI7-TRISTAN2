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
    def test_report_builder_is_oak_bounded(self) -> None:
        report = bench.build_report([0.0], include_fixture=True)
        payload = bench.asdict(report)
        self.assertIn("synthetic", payload["datasets"])
        self.assertIn("csv_adapter_fixture", payload["datasets"])
        self.assertTrue(payload["classification_results"])
        self.assertTrue(payload["compression_results"])
        self.assertIn("No general superiority", payload["oak_boundary"])

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
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "ffwt-hac-cvcd-benchmark-v0.1")
            self.assertIn("M-minus", out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
