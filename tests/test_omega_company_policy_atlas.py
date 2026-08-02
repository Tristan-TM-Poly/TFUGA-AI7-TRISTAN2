import json
from pathlib import Path

from omega_company_autopilot_t.policy_atlas import PolicyAtlas


def test_policy_atlas_decode_and_audit(tmp_path: Path):
    root = tmp_path / "atlas"
    manifest = {
        "layers": ["plan", "gate", "evidence"],
        "division_codes": {"d00": "oak"},
        "process_codes": {"p00": "reporting"},
        "risk_codes": {"r00": "low", "r01": "high"},
        "cells_per_file": 12
    }
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    cells = "\n".join(f"r{risk:02d}|l{level}" for risk in range(2) for level in range(6)) + "\n"
    for layer in manifest["layers"]:
        path = root / layer / "d00"
        path.mkdir(parents=True)
        (path / "p00.cells").write_text(cells, encoding="utf-8")
    atlas = PolicyAtlas(root)
    cell = atlas.decode(root / "gate" / "d00" / "p00.cells", 8)
    assert cell.risk_mode == "high"
    assert cell.autonomy_level == 1
    assert atlas.audit()["record_count"] == 36
