from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_m_plus_mentions_dry_run_first():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_M_PLUS.md").read_text(encoding="utf-8")
    assert "dry-run" in text
    assert "PR-only CI" in text
