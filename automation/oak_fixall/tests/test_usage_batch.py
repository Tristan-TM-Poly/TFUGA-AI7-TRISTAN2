from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_usage_batch_mentions_batch_report():
    text = (ROOT / "automation" / "oak_fixall" / "USAGE_BATCH.md").read_text(encoding="utf-8")
    assert "batch_report.py" in text
