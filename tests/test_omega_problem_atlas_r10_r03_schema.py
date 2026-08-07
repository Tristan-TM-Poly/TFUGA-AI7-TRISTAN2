from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from omega_millennium_t.r03 import compile_max_atlas
from omega_millennium_t.r10 import ingest_r03_max
from omega_millennium_t.r10.model import RuntimePolicy


def test_r03_stream_manifest_and_report_validate(tmp_path: Path) -> None:
    source = tmp_path / "r03"
    compile_max_atlas(source)
    output = tmp_path / "r10"
    ingest_r03_max(
        source,
        output,
        policy=RuntimePolicy(batch_size=500, shard_target_bytes=131_072),
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    manifest_schema = json.loads(
        Path("schemas/omega_problem_stream_manifest_v10.schema.json").read_text(encoding="utf-8")
    )
    report_schema = json.loads(
        Path("schemas/omega_problem_stream_report_v10.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(manifest, manifest_schema)
    jsonschema.validate(report, report_schema)
