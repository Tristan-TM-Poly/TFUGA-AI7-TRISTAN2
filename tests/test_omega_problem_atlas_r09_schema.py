from __future__ import annotations

import json
import runpy
from pathlib import Path

import jsonschema

from omega_millennium_t.r09 import compile_promotion_gate


def test_bundle_and_report_validate_against_closed_schemas(tmp_path: Path) -> None:
    fixtures = runpy.run_path("tests/test_omega_problem_atlas_r09_promotion_gate.py")
    bundle = fixtures["_build_bundle"]()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")

    bundle_schema = json.loads(
        Path("schemas/omega_problem_promotion_bundle_v9.schema.json").read_text(encoding="utf-8")
    )
    report_schema = json.loads(
        Path("schemas/omega_problem_promotion_report_v9.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(bundle, bundle_schema)

    output = tmp_path / "output"
    compile_promotion_gate(bundle_path, output)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    jsonschema.validate(report, report_schema)
