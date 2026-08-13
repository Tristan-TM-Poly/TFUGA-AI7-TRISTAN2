import json
from dataclasses import fields
from pathlib import Path

from sage_tristan.tensor_research_self_model import (
    CreditReceipt,
    CreditUnit,
    MemoryClass,
    OutcomeClass,
    PredictionReceipt,
    ValueOfComputationReceipt,
)


SCHEMA_PATH = Path("schemas/tensor_research_self_model_r08.schema.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _field_names(cls):
    return {item.name for item in fields(cls)}


def test_schema_parses_and_declares_r08():
    schema = _schema()
    assert schema["title"] == "Omega Tensor Research Self-Model R0.8"
    assert schema["properties"]["release"]["const"] == "R0.8"


def test_enum_contracts_align():
    defs = _schema()["$defs"]
    assert set(defs["OutcomeClass"]["enum"]) == {item.value for item in OutcomeClass}
    assert set(defs["MemoryClass"]["enum"]) == {item.value for item in MemoryClass}
    assert set(defs["CreditUnit"]["enum"]) == {item.value for item in CreditUnit}


def test_credit_receipt_schema_aligns_and_forbids_causal_promotion():
    definition = _schema()["$defs"]["CreditReceipt"]
    assert set(definition["properties"]) == _field_names(CreditReceipt)
    assert set(definition["required"]) == _field_names(CreditReceipt)
    assert definition["properties"]["causal_credit_proven"]["const"] is False
    assert definition["properties"]["confounding_possible"]["const"] is True
    assert definition["properties"]["observational_only"]["const"] is True


def test_prediction_schema_aligns_and_forbids_causality_external_validity():
    definition = _schema()["$defs"]["PredictionReceipt"]
    assert set(definition["properties"]) == _field_names(PredictionReceipt)
    assert set(definition["required"]) == _field_names(PredictionReceipt)
    assert definition["properties"]["predictive_association_only"]["const"] is True
    assert definition["properties"]["causal_effect_proven"]["const"] is False
    assert definition["properties"]["external_validity_proven"]["const"] is False


def test_voc_schema_aligns_and_forbids_guaranteed_return():
    definition = _schema()["$defs"]["ValueOfComputationReceipt"]
    assert set(definition["properties"]) == _field_names(ValueOfComputationReceipt)
    assert set(definition["required"]) == _field_names(ValueOfComputationReceipt)
    assert definition["properties"]["policy_proxy_only"]["const"] is True
    assert definition["properties"]["causal_effect_proven"]["const"] is False
    assert definition["properties"]["guaranteed_positive_return"]["const"] is False


def test_root_forbids_overclaims():
    props = _schema()["properties"]
    assert props["append_only_episode_ledger"]["const"] is True
    assert props["m_plus_is_truth"]["const"] is False
    assert props["m_minus_is_permanent_refutation"]["const"] is False
    assert props["m_question_preserved"]["const"] is True
    assert props["credit_is_causal_proof"]["const"] is False
    assert props["prediction_is_causal_effect"]["const"] is False
    assert props["value_of_computation_is_guaranteed_return"]["const"] is False
    assert props["benchmark_history_is_external_scientific_validation"]["const"] is False
    assert props["upstream_r07_required"]["const"] is True
