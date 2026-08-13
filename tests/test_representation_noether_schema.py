import json
from dataclasses import fields
from pathlib import Path

from sage_tristan.greatsages import ClaimClass
from sage_tristan.representation_noether_compiler import (
    InvariantMeasurement,
    MetricKind,
    RepresentationMorphismR05,
)


SCHEMA = Path("schemas/representation_morphism_r05.schema.json")


def test_schema_parses_and_matches_runtime_enums():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["claim_class"]["enum"] == [item.value for item in ClaimClass]
    assert schema["properties"]["metric_kind"]["enum"] == [item.value for item in MetricKind]


def test_schema_required_fields_match_runtime_morphism_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    runtime = {item.name for item in fields(RepresentationMorphismR05)}
    assert set(schema["required"]) == runtime


def test_schema_invariant_fields_match_runtime_measurement_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    runtime = {item.name for item in fields(InvariantMeasurement)}
    assert set(schema["$defs"]["invariantMeasurement"]["required"]) == runtime


def test_schema_oak_boundary_rejects_overclaiming():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    boundary = schema["x-oak-boundary"].lower()
    assert "never a physical conservation law" in boundary
    assert "mathematical theorem" in boundary
    assert "cognitive law" in boundary
