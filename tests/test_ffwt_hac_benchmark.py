from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "prototypes" / "omega_ffwt_hac_cvcd" / "run_ffwt_hac_benchmark.py"


def test_ffwt_cli_generates_oak_bounded_reports() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_json = Path(tmpdir) / "benchmark.json"
        out_md = Path(tmpdir) / "benchmark.md"
        subprocess.run(
            [sys.executable, str(SCRIPT), "--noise-levels", "0.0,0.05", "--output", str(out_json), "--markdown-output", str(out_md)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["version"] == "ffwt-hac-cvcd-benchmark-v0.1"
        assert payload["classification_results"]
        assert payload["ablation_summary"]
        assert payload["compression_results"]
        assert "No general superiority" in payload["oak_boundary"]
        assert "M-minus" in out_md.read_text(encoding="utf-8")
