import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_report_cli_generates_files(tmp_path):
    example = ROOT / "automation" / "oak_fixall" / "examples" / "clean_merge_candidate.decision.json"
    json_out = tmp_path / "summary.json"
    md_out = tmp_path / "summary.md"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "automation" / "oak_fixall" / "batch_report.py"),
            str(example),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=True,
        cwd=ROOT,
    )
    summary = json.loads(json_out.read_text(encoding="utf-8"))
    assert summary["total_items"] == 1
    assert "MERGE_NOW" in md_out.read_text(encoding="utf-8")
