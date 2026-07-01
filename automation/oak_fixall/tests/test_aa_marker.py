from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_aa_marker_exists():
    path = ROOT / "automation" / "oak_fixall" / "AA.txt"
    assert path.exists()
