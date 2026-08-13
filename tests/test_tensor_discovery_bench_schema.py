import json
from dataclasses import fields
from pathlib import Path

from sage_tristan.tensor_discovery_bench import (
    AblationReceipt,
    BenchmarkFamily,
    BenchmarkRun,
    BenchmarkTask,
    ContaminationTensor,
    ExposureStatus,
    SystemKind,
)


SCHEMA_PATH = Path("schemas/tensor_discovery_bench_r07.schema.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _field_names(cls):
    return {item.name for item in fields(cls)}


def test_schema_parses_and_declares_r07():
    schema = _schema()
    assert schema["title"] == "Omega Tensor DiscoveryBench R0.7"
    assert schema["properties"]["release"]["const"] == "R0.7"


def test_enum_contracts_align_with_runtime():
    schema = _schema()["$defs"]
    assert set(schema["BenchmarkFamily"]["enum"]) == {item.value for item in BenchmarkFamily}
    assert set(schema["SystemKind"]["enum"]) == {item.value for item in SystemKind}
    assert set(schema["ExposureStatus"]["enum"]) == {item.value for item in ExposureStatus}


def test_contamination_tensor_fields_align():
    definition = _schema()["$defs"]["ContaminationTensor"]
    assert set(definition["properties"]) == _field_names(ContaminationTensor)
    assert set(definition["required"]) == _field_names(ContaminationTensor)


def test_task_fields_align():
    definition = _schema()["$defs"]["BenchmarkTask"]
    assert set(definition["properties"]) == _field_names(BenchmarkTask)
    assert set(definition["required"]) == _field_names(BenchmarkTask)
    assert definition["properties"]["human_novelty_claimed"]["const"] is False
    assert definition["properties"]["novelty_scope"]["const"] == "benchmark_only"


def test_run_fields_align_and_forbid_overclaims():
    definition = _schema()["$defs"]["BenchmarkRun"]
    assert set(definition["properties"]) == _field_names(BenchmarkRun)
    assert set(definition["required"]) == _field_names(BenchmarkRun)
    assert definition["properties"]["human_novelty_claimed"]["const"] is False
    assert definition["properties"]["independent_discovery_claimed"]["const"] is False
    assert definition["properties"]["benchmark_proxy_only"]["const"] is True


def test_ablation_schema_forbids_causal_promotion():
    definition = _schema()["$defs"]["AblationReceipt"]
    assert set(definition["properties"]) == _field_names(AblationReceipt)
    assert set(definition["required"]) == _field_names(AblationReceipt)
    assert definition["properties"]["causal_effect_proven"]["const"] is False


def test_root_schema_forbids_scalar_intelligence_and_meta_superiority_claims():
    properties = _schema()["properties"]
    assert properties["scalar_intelligence_score_produced"]["const"] is False
    assert properties["human_novelty_claimed"]["const"] is False
    assert properties["independent_discovery_certified"]["const"] is False
    assert properties["meta_llmt_automatically_superior"]["const"] is False
    assert properties["benchmark_proxy_only"]["const"] is True
