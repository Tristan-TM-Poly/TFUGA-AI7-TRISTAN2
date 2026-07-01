from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_m_minus_contains_stale_decision_warning():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_M_MINUS.md").read_text(encoding="utf-8")
    assert "stale decision" in text
    assert "not to replace" in text
