from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_marker_file_exists():
    assert (ROOT / "automation" / "oak_fixall" / "MARKER.txt").exists()
