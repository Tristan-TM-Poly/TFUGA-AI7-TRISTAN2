from __future__ import annotations

import json
from pathlib import Path

from omega_synergy_t.cli import build_parser, run


def test_cli_legacy_flags_generate_bundle(tmp_path: Path) -> None:
    (tmp_path / "systems.md").write_text(
        "Ω-A-T transforms document -> claim graph.\n"
        "Ω-B-T needs document -> claim graph.\n"
        "Ω-C-T transforms claim graph -> evidence report.\n",
        encoding="utf-8",
    )
    parser = build_parser()
    args = parser.parse_args([
        "--repo-root", str(tmp_path),
        "--out", "reports/test",
        "--max-order", "3",
        "--beam-width", "12",
        "--top-k", "5",
        "--max-nodes", "30",
    ])
    summary = run(args)
    assert summary["creations"] >= 3
    payload = json.loads((tmp_path / "reports" / "test" / "synergy_report.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["authority"] == "review_only_heuristic"
