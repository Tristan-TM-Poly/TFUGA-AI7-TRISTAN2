from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_final_marker_exists():
    path = ROOT / "automation" / "oak_fixall" / "FINAL.txt"
    assert path.exists()
