from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_note_exists():
    assert (ROOT / "automation" / "oak_fixall" / "NOTE.md").exists()
