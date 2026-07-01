from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_w_file_exists():
    assert (ROOT / "automation" / "oak_fixall" / "W.txt").exists()
