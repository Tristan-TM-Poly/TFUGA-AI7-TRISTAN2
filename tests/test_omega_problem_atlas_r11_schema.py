from __future__ import annotations

import json
import runpy
from pathlib import Path

import jsonschema

from omega_millennium_t.r11 import compile_competition_ledger


def _schema(name: str) -> dict:
    return json.loads(Path("schemas", name).read_text(encoding="utf-8"))


def test_bundle_manifest_and_report_validate_against_closed_schemas(tmp_path: Path) -> None:
    fixtures = runpy.run_path("tests/test_omega_problem_atlas_r11_competition_ledger.py")
    bundle = fixtures["_build_bundle"]()
    jsonschema.validate(
        bundle,
        _schema("omega_competition_ledger_bundle_v11.schema.json"),
    )

    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / "output"
    compile_competition_ledger(bundle_path, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    jsonschema.validate(
        manifest,
        _schema("omega_competition_ledger_manifest_v11.schema.json"),
    )
    jsonschema.validate(
        report,
        _schema("omega_competition_ledger_report_v11.schema.json"),
    )
