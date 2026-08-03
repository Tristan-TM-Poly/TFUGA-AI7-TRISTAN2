from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from omega_millennium_t.r10 import materialize_synthetic_campaign
from omega_millennium_t.r10.model import CELL_SCHEMA, RuntimePolicy


def _schema(name: str) -> dict:
    return json.loads(Path("schemas", name).read_text(encoding="utf-8"))


def test_cell_manifest_and_report_validate_against_closed_schemas(tmp_path: Path) -> None:
    cell = {
        "schema": CELL_SCHEMA,
        "cell_id": "cell::fixture",
        "problem_id": "problem::fixture",
        "target_id": "target::fixture",
        "front": "analysis",
        "method": "exact",
        "priority": 10,
        "source_ref": "fixture://cell",
        "payload": {"fixture": True},
    }
    jsonschema.validate(cell, _schema("omega_problem_stream_cell_v10.schema.json"))

    output = tmp_path / "output"
    materialize_synthetic_campaign(
        output,
        cell_count=1_000,
        policy=RuntimePolicy(batch_size=100, shard_target_bytes=32_768),
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    jsonschema.validate(manifest, _schema("omega_problem_stream_manifest_v10.schema.json"))
    jsonschema.validate(report, _schema("omega_problem_stream_report_v10.schema.json"))


def test_already_complete_report_validates(tmp_path: Path) -> None:
    output = tmp_path / "output"
    policy = RuntimePolicy(batch_size=50, shard_target_bytes=16_384)
    materialize_synthetic_campaign(output, cell_count=100, policy=policy)
    report = materialize_synthetic_campaign(
        output,
        cell_count=100,
        policy=policy,
        resume=True,
        clean=False,
    )
    jsonschema.validate(report, _schema("omega_problem_stream_report_v10.schema.json"))
