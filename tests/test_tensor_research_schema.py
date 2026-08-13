import json
from dataclasses import fields
from pathlib import Path

from sage_tristan.tensor_research_compiler import (
    CognitiveProgram,
    Instruction,
    Opcode,
    PermissionScope,
    PersonLLMT,
    ShadowMirror,
    ShadowRole,
    ShadowSpec,
    ValueType,
)


SCHEMA = Path("schemas/tensor_research_compiler_r06.schema.json")


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_parses_and_has_oak_boundary():
    schema = _schema()
    assert schema["title"] == "Omega Tensor Research Compiler R0.6"
    assert "PersonLLMT is not a person" in schema["x-oak-boundary"]


def test_runtime_enums_match_schema():
    schema = _schema()["$defs"]
    assert set(schema["personLLMT"]["properties"]["permission_scope"]["enum"]) == {x.value for x in PermissionScope}
    assert set(schema["shadowSpec"]["properties"]["role"]["enum"]) == {x.value for x in ShadowRole}
    assert set(schema["shadowSpec"]["properties"]["mirror"]["enum"]) == {x.value for x in ShadowMirror}
    assert set(schema["instruction"]["properties"]["opcode"]["enum"]) == {x.value for x in Opcode}
    assert set(schema["instruction"]["properties"]["input_type"]["enum"]) == {x.value for x in ValueType}
    assert set(schema["instruction"]["properties"]["output_type"]["enum"]) == {x.value for x in ValueType}


def test_required_fields_match_dataclasses():
    schema = _schema()["$defs"]
    assert set(schema["personLLMT"]["required"]) == {f.name for f in fields(PersonLLMT)}
    assert set(schema["shadowSpec"]["required"]) == {f.name for f in fields(ShadowSpec)}
    assert set(schema["instruction"]["required"]) == {f.name for f in fields(Instruction)}
    assert set(schema["cognitiveProgram"]["required"]) == {f.name for f in fields(CognitiveProgram)}


def test_schema_hard_codes_non_impersonation_flags():
    schema = _schema()["$defs"]
    assert schema["personLLMT"]["properties"]["model_not_person"]["const"] is True
    assert schema["personLLMT"]["properties"]["historical_mind_certified"]["const"] is False
    assert schema["shadowSpec"]["properties"]["ephemeral"]["const"] is True
    assert schema["shadowSpec"]["properties"]["model_not_person"]["const"] is True
