from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_q_marker_file_exists():
    path = ROOT / "automation" / "oak_fixall" / "Q.txt"
    assert path.exists()
