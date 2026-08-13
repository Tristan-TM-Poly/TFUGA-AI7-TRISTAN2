from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_capability_os_t.core import Capability
from omega_research_abi_t.adapters import BRIDGE_BOUNDARY, adapt_capability, adapt_snapshot
from omega_research_abi_t.cli import compile_fixture
from omega_research_abi_t.compiler import ResearchABICompiler
from omega_research_abi_t.core import Envelope, GraphEdge, InvariantCheck
from omega_research_abi_t.graphs import ResearchGraphKernel
from omega_research_abi_t.receipts import ReceiptError, issue_receipt, validate_receipt


def test_envelope_fingerprint_is_deterministic() -> None:
    a = Envelope(graph="knowledge", object_type="claim", object_id="c1", payload={"b": 2, "a": 1})
    b = Envelope(graph="knowledge", object_type="claim", object_id="c1", payload={"a": 1, "b": 2})
    assert a.content_hash == b.content_hash
    assert a.ref.key == "knowledge:claim:c1"


def test_six_graph_kernel_keeps_types_distinct_and_links_cross_graph() -> None:
    kernel = ResearchGraphKernel()
    claim = kernel.add(Envelope(graph="knowledge", object_type="claim", object_id="c", payload={"x": 1}))
    work = kernel.add(Envelope(graph="work", object_type="work_unit", object_id="w", payload={"x": 1}))
    kernel.link(GraphEdge(source=claim, target=work, relation="motivates"))
    report = kernel.validate()
    assert report["status"] == "PASS"
    assert report["node_counts"]["knowledge"] == 1
    assert report["node_counts"]["work"] == 1


def test_kernel_refuses_missing_endpoint_and_causal_without_evidence() -> None:
    kernel = ResearchGraphKernel()
    claim = kernel.add(Envelope(graph="knowledge", object_type="claim", object_id="c", payload={}))
    missing = Envelope(graph="work", object_type="work_unit", object_id="missing", payload={}).ref
    with pytest.raises(KeyError):
        kernel.link(GraphEdge(source=claim, target=missing, relation="supports"))
    with pytest.raises(ValueError):
        GraphEdge(source=claim, target=missing, relation="causes", causal_claim=True)


def test_receipt_oak_pass_requires_passed_invariants() -> None:
    ref = Envelope(graph="work", object_type="work_unit", object_id="w", payload={}).ref
    with pytest.raises(ReceiptError):
        issue_receipt(
            operator="bad",
            inputs=(ref,),
            outputs=(ref,),
            invariants=(InvariantCheck("semantic_preservation", "UNKNOWN"),),
            oak_state="PASS",
        )


def test_mutation_receipt_requires_explicit_rollback_statement() -> None:
    ref = Envelope(graph="work", object_type="work_unit", object_id="w", payload={}).ref
    with pytest.raises(ReceiptError):
        issue_receipt(operator="write", inputs=(ref,), outputs=(ref,), authority="write")
    receipt = issue_receipt(
        operator="write",
        inputs=(ref,),
        outputs=(ref,),
        authority="write",
        rollback="git revert <sha>",
        risk=0.2,
    )
    assert validate_receipt(receipt)["status"] == "PASS"


def test_capability_adapter_reuses_existing_ontology() -> None:
    cap = Capability(
        capability_id="x.reuse",
        domains=("research",),
        consumes=("intent",),
        produces=("result",),
        authority="read",
    )
    env = adapt_capability(cap, provenance=("PR#417",))
    assert env.graph == "capability"
    assert env.payload["source_ontology"] == "omega_capability_os_t.core.Capability"
    assert env.payload["produces"] == ("result",)


def test_snapshot_adapter_keeps_hard_boundary() -> None:
    env = adapt_snapshot(
        component="discovery_os",
        graph="knowledge",
        object_type="claim",
        object_id="x",
        payload={"score": 1.0},
        provenance=("PR#444",),
    )
    assert env.payload["bridge_boundary"] == BRIDGE_BOUNDARY
    assert env.payload["source_component"] == "discovery_os"


def test_context_packet_is_bounded_and_deterministic() -> None:
    compiler = ResearchABICompiler()
    for index in range(5):
        compiler.add_object(Envelope(
            graph="knowledge",
            object_type="claim",
            object_id=f"c{index}",
            payload={"i": index},
        ))
    first = compiler.compile(max_per_graph=2)
    second = compiler.compile(max_per_graph=2)
    assert first["context"]["omitted"]["knowledge"] == 3
    assert first["fingerprint"] == second["fingerprint"]


def test_end_to_end_fixture_compiles_all_six_graphs_and_receipt() -> None:
    payload = json.loads(Path("examples/research_abi_fixture.json").read_text(encoding="utf-8"))
    result = compile_fixture(payload)
    counts = result["graph_validation"]["node_counts"]
    assert set(counts) == {"knowledge", "capability", "work", "experiment", "provenance", "value"}
    assert all(counts[kind] == 1 for kind in counts)
    assert result["graph_validation"]["status"] == "PASS"
    assert result["receipts"][0]["validation"]["status"] == "PASS"
