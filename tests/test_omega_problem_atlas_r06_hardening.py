from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r06 import audit_evidence_graph, compile_evidence_graph


def _canonical(path: Path) -> Path:
    row = {
        "canonical_problem_id": "problem::alpha",
        "canonical_record_id": "record::alpha",
        "member_record_ids": ["record::alpha"],
        "titles": ["Alpha"],
        "alias_keys": [],
        "fronts": ["graphs_hypergraphs"],
        "statement_fingerprints": [],
        "identity_status": "singleton",
        "member_count": 1,
        "proof_claimed": False,
        "solution_claimed": False,
        "canonical_digest": "fixture-canonical-digest",
    }
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _node(node_id: str, node_type: str, metadata: dict) -> dict:
    return {
        "node_id": node_id,
        "node_type": node_type,
        "canonical_problem_id": "problem::alpha",
        "title": node_id,
        "content": f"Content for {node_id}",
        "scope": "fixture",
        "source_refs": [f"fixture:{node_id}"],
        "observed_at": "2026-08-03T16:00:00Z",
        "metadata": metadata,
        "proof_claimed": False,
        "solution_claimed": False,
    }


def _edge(edge_id: str, source: str, target: str, relation: str) -> dict:
    return {
        "edge_id": edge_id,
        "source_node_id": source,
        "target_node_id": target,
        "relation": relation,
        "scope": "fixture",
        "evidence_refs": [f"fixture:{edge_id}"],
        "metadata": {},
    }


def _bundle(path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "omega-problem-evidence-bundle/6",
                "bundle_id": "hardening-fixture",
                "nodes": nodes,
                "edges": edges,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_computation_receipt_requires_run_digest(tmp_path: Path) -> None:
    canonical = _canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.one", "claim", {"requested_status": "experimental"}),
        _node(
            "computation.one",
            "computation_receipt",
            {"outcome": "success", "certificate_verified": False},
        ),
    ]
    bundle = _bundle(
        tmp_path / "bundle.json",
        nodes,
        [_edge("edge.support", "computation.one", "claim.one", "supports")],
    )
    with pytest.raises(ValueError, match="requires run_digest"):
        compile_evidence_graph(canonical, (bundle,), tmp_path / "output")


def test_kernel_checked_artifact_requires_named_verifier(tmp_path: Path) -> None:
    canonical = _canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.one", "claim", {"requested_status": "formal_restricted"}),
        _node(
            "formal.one",
            "formal_artifact",
            {"proof_scope": "restricted", "kernel_checked": True},
        ),
    ]
    bundle = _bundle(
        tmp_path / "bundle.json",
        nodes,
        [_edge("edge.proves", "formal.one", "claim.one", "proves_restricted_case")],
    )
    with pytest.raises(ValueError, match="requires verifier"):
        compile_evidence_graph(canonical, (bundle,), tmp_path / "output")


def test_independent_review_requires_reviewer_and_scope(tmp_path: Path) -> None:
    canonical = _canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.one", "claim", {"requested_status": "candidate"}),
        _node("review.one", "independent_review", {"outcome": "accepted"}),
    ]
    bundle = _bundle(
        tmp_path / "bundle.json",
        nodes,
        [_edge("edge.review", "review.one", "claim.one", "supports")],
    )
    with pytest.raises(ValueError, match="requires reviewer"):
        compile_evidence_graph(canonical, (bundle,), tmp_path / "output")


def test_claim_cannot_be_used_as_evidence_source(tmp_path: Path) -> None:
    canonical = _canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.source", "claim", {"requested_status": "candidate"}),
        _node("claim.target", "claim", {"requested_status": "candidate"}),
    ]
    bundle = _bundle(
        tmp_path / "bundle.json",
        nodes,
        [_edge("edge.invalid", "claim.source", "claim.target", "supports")],
    )
    with pytest.raises(ValueError, match="non-evidential source"):
        compile_evidence_graph(canonical, (bundle,), tmp_path / "output")


def test_canonical_identity_reference_tampering_is_detected(tmp_path: Path) -> None:
    canonical = _canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.one", "claim", {"requested_status": "experimental"}),
        _node("evidence.one", "evidence", {"evidence_kind": "numerical"}),
    ]
    bundle = _bundle(
        tmp_path / "bundle.json",
        nodes,
        [_edge("edge.support", "evidence.one", "claim.one", "supports")],
    )
    output = tmp_path / "output"
    compile_evidence_graph(canonical, (bundle,), output)
    refs_path = output / "canonical_identity_refs.jsonl"
    row = json.loads(refs_path.read_text(encoding="utf-8"))
    row["member_count"] = 99
    refs_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    audit = audit_evidence_graph(output)
    assert audit["valid"] is False
    assert any(
        "canonical_identity_refs.jsonl: sha256 mismatch" in error
        or "identity reference digest mismatch" in error
        for error in audit["errors"]
    )
