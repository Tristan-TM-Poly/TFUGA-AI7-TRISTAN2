from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from omega_capability_os_t.core import load_registry, validate_registry
from omega_capability_os_t.github_memory_evolution import (
    ResidualArtifactSpec,
    ReuseOutcomeReceipt,
)
from omega_research_abi_t.cli import compile_fixture
from omega_research_abi_t.core import Envelope
from omega_research_abi_t.github_memory_bridge import (
    GITHUB_MEMORY_R07_BOUNDARY,
    adapt_llmt_federation,
    adapt_residual_artifact_spec,
    adapt_reuse_outcome,
    adapt_supersession_report,
)
from omega_research_abi_t.ledger import ResearchTransitionLedger
from omega_research_abi_t.receipts import issue_receipt


def test_residual_artifact_spec_reuses_r07_ontology_without_write_authority() -> None:
    spec = ResidualArtifactSpec(
        request_id="req:r02",
        decision="EXTEND",
        selected_capabilities=("github.reuse_before_create",),
        residual_outputs=("research_abi",),
        exact_inspection_refs=("PR#447",),
        required_tests=("exact-head CI",),
        required_provenance=("PR#447",),
        generation_scope="residual_outputs_only",
        generation_allowed=True,
        boundary="generation_allowed != GitHub write authority",
    )
    env = adapt_residual_artifact_spec(spec)
    assert env.graph == "work"
    assert env.authority == "draft"
    assert env.payload["source_ontology"].endswith("ResidualArtifactSpec")
    assert env.payload["bridge_boundary"] == GITHUB_MEMORY_R07_BOUNDARY


def test_reuse_outcome_is_experiment_evidence_not_causal_proof() -> None:
    outcome = ReuseOutcomeReceipt(
        receipt_id="outcome:r02",
        request_id="req:r02",
        action="REUSE",
        selected_capabilities=("github.reuse_before_create",),
        outcome="SUCCESS",
        evidence_refs=("ci:run:123",),
    )
    env = adapt_reuse_outcome(outcome, uncertainty=0.1)
    assert env.graph == "experiment"
    assert env.payload["memory_class"] == "M+"
    assert env.payload["utility"] == 1.0
    assert env.provenance == ("ci:run:123",)
    assert "causal_proof" in env.payload["bridge_boundary"]


def test_review_only_supersession_is_hold_and_llmt_federation_is_draft() -> None:
    supersession = adapt_supersession_report({
        "fingerprint": "supersession:r02",
        "candidate_count": 1,
        "strong_edges_added": 0,
    })
    federation = adapt_llmt_federation({
        "fingerprint": "federation:r02",
        "packet_count": 3,
    })
    assert supersession.graph == "provenance"
    assert supersession.oak_state == "HOLD"
    assert federation.graph == "work"
    assert federation.authority == "draft"
    assert "independent_evidence" in federation.payload["bridge_boundary"]


def test_transition_ledger_verifies_continuity_and_detects_tampering() -> None:
    ref = Envelope(graph="work", object_type="work_unit", object_id="w", payload={}).ref
    first = issue_receipt(operator="t1", inputs=(ref,), outputs=(ref,))
    second = issue_receipt(operator="t2", inputs=(ref,), outputs=(ref,))
    ledger = ResearchTransitionLedger()
    entry0 = ledger.append(first, state_before="S0", state_after="S1")
    ledger.append(second, state_before="S1", state_after="S2")
    assert ledger.verify()["status"] == "PASS"
    assert ledger.trace_state("S1") == tuple(ledger.entries)

    ledger.entries[0] = replace(entry0, state_after="TAMPERED")
    report = ledger.verify()
    assert report["status"] == "FAIL"
    assert any("chain hash mismatch" in error for error in report["errors"])
    assert any("state continuity mismatch" in error for error in report["errors"])


def test_reference_fixture_emits_verified_transition_chain() -> None:
    payload = json.loads(Path("examples/research_abi_fixture.json").read_text(encoding="utf-8"))
    result = compile_fixture(payload)
    ledger = result["transition_ledger"]
    assert result["abi"] == "omega-universal-research-abi-r02"
    assert ledger["verification"]["status"] == "PASS"
    assert ledger["verification"]["entry_count"] == 1
    assert result["receipts"][0]["ledger_entry"]["state_before"] == "state:reuse-memory-r07"


def test_live_capability_registry_passes_and_self_registers_r02() -> None:
    payload = json.loads(Path("examples/capability_os_registry.json").read_text(encoding="utf-8"))
    registry = load_registry(payload)
    report = validate_registry(registry)
    assert report["status"] == "PASS", report["errors"]
    ids = {cap.capability_id for cap in registry}
    assert {
        "research_abi.object.envelope",
        "research_abi.six_graph.compile",
        "research_abi.receipt.issue",
        "research_abi.receipt.verify",
        "research_abi.snapshot.bridge",
        "research_abi.context.compile",
        "research_abi.github_memory_r07.bridge",
        "research_abi.transition_ledger.append_verify",
    } <= ids
