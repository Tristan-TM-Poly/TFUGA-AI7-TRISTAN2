from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_oak_notes_warns_advisory_only():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_OAK_NOTES.md").read_text(encoding="utf-8")
    assert "advisory only" in text
    assert "live GitHub verification" in text
