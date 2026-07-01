from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_x_marker_file_exists():
    path = ROOT / "automation" / "oak_fixall" / "X.txt"
    assert path.exists()
