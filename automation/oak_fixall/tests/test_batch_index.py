from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_index_mentions_three_layers():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_INDEX.md").read_text(encoding="utf-8")
    assert "Decision validation" in text
    assert "Batch reporting" in text
    assert "OAK memory" in text
