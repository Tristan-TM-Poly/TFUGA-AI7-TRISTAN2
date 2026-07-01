from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_todo_preserves_observe_first_rule():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_TODO.md").read_text(encoding="utf-8")
    assert "observe first" in text
    assert "OAK verification" in text
