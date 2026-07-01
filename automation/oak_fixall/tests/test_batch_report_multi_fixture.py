import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_report_cli_summarizes_input_list(tmp_path):
    list_path = ROOT / "automation" / "oak_fixall" / "examples" / "batch_input_list.txt"
    paths = [str(ROOT / line.strip()) for line in list_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    json_out = tmp_path / "batch.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "automation" / "oak_fixall" / "batch_report.py"),
            *paths,
            "--json-out",
            str(json_out),
        ],
        check=True,
        cwd=ROOT,
    )
    summary = json.loads(json_out.read_text(encoding="utf-8"))
    assert summary["total_items"] >= 4
    assert summary["decision_counts"]["MERGE_NOW"] >= 1
    assert summary["decision_counts"]["WAIT_COOLDOWN"] >= 1
    assert summary["decision_counts"]["BLOCK_M_MINUS"] >= 1
