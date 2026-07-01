from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_t_marker_file_exists():
    path = ROOT / "automation" / "oak_fixall" / "T.txt"
    assert path.exists()
