from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pr2_marker_exists():
    assert (ROOT / "automation" / "oak_fixall" / "PR2.txt").exists()
