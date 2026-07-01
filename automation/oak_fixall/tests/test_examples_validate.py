import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "automation" / "oak_fixall"))

from validate_decision import validate_decision  # noqa: E402


def test_all_example_decisions_validate_required_shape():
    example_dir = ROOT / "automation" / "oak_fixall" / "examples"
    files = sorted(example_dir.glob("*.decision.json"))
    assert files
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_decision(data)
        assert not errors, f"{path}: {errors}"
