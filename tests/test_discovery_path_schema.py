import json
from dataclasses import asdict
from pathlib import Path

from sage_tristan.discovery_path_ir import gauss_ceres_reconstruction
from sage_tristan.greatsages import ClaimClass


SCHEMA_PATH = Path("schemas/discovery_path_r04.schema.json")


def test_schema_is_valid_json_and_has_oak_boundary():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["title"] == "Omega Discovery Path IR R0.4"
    assert "x-oak-boundary" in schema
    assert "historical causation" in schema["x-oak-boundary"]


def test_schema_claim_classes_match_runtime_exactly():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_values = set(schema["properties"]["claim_class"]["enum"])
    runtime_values = {item.value for item in ClaimClass}
    assert schema_values == runtime_values


def test_runtime_fixture_contains_all_schema_required_fields():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = asdict(gauss_ceres_reconstruction())
    assert set(schema["required"]) <= set(payload)
    assert set(schema["$defs"]["epistemicState"]["required"]) <= set(payload["states"][0])
    assert set(schema["$defs"]["pathStep"]["required"]) <= set(payload["steps"][0])
    assert set(schema["$defs"]["resourceCost"]["required"]) <= set(payload["steps"][0]["cost"])
    assert set(schema["$defs"]["residualVector"]["required"]) <= set(payload["steps"][0]["residuals"])
