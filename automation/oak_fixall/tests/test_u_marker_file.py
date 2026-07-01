from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_u_marker_file_exists():
    path = ROOT / "automation" / "oak_fixall" / "U.txt"
    assert path.exists()
