from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pr3_marker_exists():
    assert (ROOT / "automation" / "oak_fixall" / "PR3.txt").exists()
