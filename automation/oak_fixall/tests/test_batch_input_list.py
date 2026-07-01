from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_input_list_points_to_existing_decisions():
    list_path = ROOT / "automation" / "oak_fixall" / "examples" / "batch_input_list.txt"
    entries = [line.strip() for line in list_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert entries
    for entry in entries:
        path = ROOT / entry
        assert path.exists(), entry
        assert path.name.endswith(".decision.json")
