from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from omega_discovery_kernel_t import (
    DiscoveryEvent,
    DiscoveryLedger,
    EVENT_TYPES,
    build_raman_closed_loop,
    claim_events_from_cell,
    generator_event_from_morph_ir,
    result_event_to_evidence_record,
)
from omega_generator_discovery_t import compile_morph_ir
from omega_wiki_t.knowledge_cell import KnowledgeCell

ROOT = Path(__file__).resolve().parents[1]


def _observation(subject: str = "SUBJECT-001") -> DiscoveryEvent:
    return DiscoveryEvent.create(
        "ObservationEvent",
        subject,
        "2026-08-02T12:00:00Z",
        source_hash="sha256:test",
        provenance=("tests/test_omega_discovery_kernel_t.py",),
        payload={"value": 1.0},
        units={"value": "dimensionless"},
        uncertainty={"value": 0.01},
    )


def test_event_ids_and_hashes_are_deterministic_and_tamper_evident() -> None:
    first = _observation()
    second = _observation()
    assert first.event_id == second.event_id
    assert first.event_hash == second.event_hash
    assert first.validate() == []

    tampered = replace(first, payload={"value": 2.0})
    assert any("hash mismatch" in issue for issue in tampered.validate())


def test_raman_demo_closes_all_eight_events_and_preserves_negative_memory() -> None:
    ledger = build_raman_closed_loop()
    assert len(ledger.events) == 8
    assert {event.event_type for event in ledger.events} == set(EVENT_TYPES)
    assert ledger.validate() == []

    audit = ledger.audit()
    assert audit.findings == []
    assert audit.metrics["closed_loop_coverage"] == 1.0
    assert audit.metrics["negative_memory_coverage"] == 1.0
    assert audit.metrics["unit_coverage"] == 1.0
    assert audit.metrics["uncertainty_coverage"] == 1.0
    assert ledger.closed_loop_status("RAMAN-TEMPERATURE-MORPH-001") == "closed_loop_recorded_not_certified"


def test_claim_requires_observation_ancestor() -> None:
    ledger = DiscoveryLedger()
    claim = DiscoveryEvent.create(
        "ClaimEvent",
        "SUBJECT-001",
        "2026-08-02T12:00:01Z",
        payload={"text": "X"},
    )
    with pytest.raises(ValueError, match="ObservationEvent"):
        ledger.append(claim)


def test_promotion_requires_result_ancestor() -> None:
    ledger = DiscoveryLedger()
    observation = ledger.append(_observation())
    transition = DiscoveryEvent.create(
        "OAKTransition",
        observation.subject_id,
        "2026-08-02T12:00:01Z",
        parent_ids=(observation.event_id,),
        payload={"from_status": "IDEA", "to_status": "DEMONSTRATED", "cause": "invalid shortcut"},
        human_approval=True,
    )
    with pytest.raises(ValueError, match="ResultPacket"):
        ledger.append(transition)


def test_mminus_requires_failed_result_or_refutation() -> None:
    ledger = DiscoveryLedger()
    observation = ledger.append(_observation())
    mminus = DiscoveryEvent.create(
        "MMinusRule",
        observation.subject_id,
        "2026-08-02T12:00:01Z",
        parent_ids=(observation.event_id,),
        payload={"reusable_rules": ["do not repeat"]},
    )
    with pytest.raises(ValueError, match="failed ResultPacket"):
        ledger.append(mminus)


def test_irreversible_experiment_requires_human_approval() -> None:
    event = DiscoveryEvent.create(
        "ExperimentSpec",
        "SUBJECT-001",
        "2026-08-02T12:00:00Z",
        payload={"name": "destructive test"},
        reversible=False,
        human_approval=False,
    )
    assert any("irreversible experiment" in issue for issue in event.validate())


def test_hyperknowledge_and_morphir_bridges_preserve_scope_and_provenance() -> None:
    cell = KnowledgeCell.read(ROOT / "data/knowledge_cells/ffwt_hac_cvcd_r0_3.json")
    observation = _observation(cell.cell_id)
    claims = claim_events_from_cell(cell, observation, timestamp="2026-08-02T12:00:01Z")
    assert len(claims) == len(cell.claims)
    assert claims[0].payload["knowledge_cell_id"] == cell.cell_id
    assert claims[0].provenance

    morph = compile_morph_ir(
        {
            "name": "ffwt_candidate",
            "domain": "signal",
            "codomain": "features",
            "continuous_generators": ["multiscale_weighting"],
            "residual": 0.1,
            "uncertainty": 0.05,
        }
    )
    generator = generator_event_from_morph_ir(morph, claims[0], timestamp="2026-08-02T12:00:02Z")
    assert generator.event_type == "GeneratorCandidate"
    assert generator.payload["continuous_generators"] == ["multiscale_weighting"]
    assert generator.uncertainty["model"] == 0.05


def test_result_packet_converts_to_hyperknowledge_counterexample() -> None:
    ledger = build_raman_closed_loop()
    result = next(event for event in ledger.events if event.event_type == "ResultPacket")
    cell = KnowledgeCell.read(ROOT / "data/knowledge_cells/ffwt_hac_cvcd_r0_3.json")
    record = result_event_to_evidence_record(result, cell.claims[0])

    assert record.kind == "counterexample"
    assert record.contradicts_claim_ids == (cell.claims[0].claim_id,)
    assert record.content_hash == result.event_hash
    assert record.metadata["baseline"]["name"] == "Lorentzian NLLS"


def test_writer_emits_manifest_ledger_graph_audit_and_report(tmp_path: Path) -> None:
    ledger = build_raman_closed_loop()
    output = ledger.write(tmp_path / "kernel")
    expected = {"manifest.json", "ledger.json", "events.jsonl", "audit.json", "graph.json", "report.md"}
    assert expected == {path.name for path in output.iterdir()}

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["event_count"] == 8
    assert manifest["ledger_hash"] == ledger.ledger_hash()
    assert manifest["oak_status"].startswith("R0.1_")
    assert "closed_loop_recorded_not_certified" in (output / "report.md").read_text(encoding="utf-8")


def test_jsonl_round_trip_preserves_ledger_hash(tmp_path: Path) -> None:
    ledger = build_raman_closed_loop()
    output = ledger.write(tmp_path / "roundtrip")
    restored = DiscoveryLedger.read_jsonl(output / "events.jsonl")
    assert restored.validate() == []
    assert restored.ledger_hash() == ledger.ledger_hash()
