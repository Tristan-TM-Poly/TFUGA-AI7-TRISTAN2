from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_summary_file_exists():
    path = ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_SUMMARY.md"
    assert path.exists()
