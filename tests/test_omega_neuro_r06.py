from dataclasses import replace

import pytest

from omega_neuro_t.public_sources import PUBLIC_SOURCES, get_public_source
from omega_neuro_t.r06_cli import build_report
from omega_neuro_t.r06_protocol import PROTOCOLS, admission_gate, get_protocol, protocol_registry


def test_primary_source_registry_is_oak_safe():
    assert set(PUBLIC_SOURCES) == {"allen_cell_types", "microns_mm3", "dandi_nwb"}
    for source in PUBLIC_SOURCES.values():
        assert source.access_mode == "public"
        assert source.provenance_review_required is True
        assert source.license_review_required is True
        assert source.automatic_biological_promotion is False


def test_protocol_digests_are_deterministic_and_semantic():
    protocol = get_protocol("P1_DENDRITIC_ADDRESS")
    assert protocol.digest() == get_protocol("P1_DENDRITIC_ADDRESS").digest()
    changed = protocol.mutated(target_definition=protocol.target_definition + " changed")
    assert changed.digest() != protocol.digest()


def test_each_protocol_only_uses_declared_source_support():
    for protocol in PROTOCOLS.values():
        for source_id in protocol.source_priority:
            assert protocol.hypothesis_id in get_public_source(source_id).candidate_hypotheses


def test_p3_is_preregistered_to_microns_not_allen():
    protocol = get_protocol("P3_HIGHER_ORDER_WIRING")
    assert protocol.source_priority == ("microns_mm3",)
    with pytest.raises(ValueError):
        admission_gate("P3_HIGHER_ORDER_WIRING", "allen_cell_types")


def test_admission_gate_never_promotes_biology():
    gate = admission_gate("P2_SYNAPTIC_STATE_TENSOR", "dandi_nwb")
    assert gate["preregistered"] is True
    assert gate["payload_hash_required"] is True
    assert gate["group_leakage_barrier_required"] is True
    assert gate["negative_control_required"] is True
    assert gate["automatic_biological_promotion"] is False
    assert gate["status"] == "ADMISSIBLE_FOR_DATA_PREPARATION_NOT_CLAIM_PROMOTION"


def test_protocol_constructor_rejects_automatic_promotion():
    protocol = get_protocol("P1_DENDRITIC_ADDRESS")
    with pytest.raises(ValueError):
        replace(protocol, automatic_biological_promotion=True)


def test_r06_report_is_deterministic_and_contains_hashes():
    first = build_report()
    second = build_report()
    assert first == second
    assert first["automatic_biological_promotion"] is False
    registry = protocol_registry()
    assert all(len(item["protocol_hash"]) == 64 for item in registry.values())


def test_r06_report_can_emit_specific_admission_gate():
    report = build_report(hypothesis="P3_HIGHER_ORDER_WIRING", source="microns_mm3")
    gate = report["admission_gate"]
    assert gate["source_id"] == "microns_mm3"
    assert gate["hypothesis_id"] == "P3_HIGHER_ORDER_WIRING"
    assert gate["automatic_biological_promotion"] is False
