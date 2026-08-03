from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r06 import audit_evidence_graph, compile_evidence_graph


def _write_canonical(path: Path, ids: tuple[str, ...] = ("problem::alpha",)) -> Path:
    rows = []
    for index, canonical_id in enumerate(ids, 1):
        row = {
            "canonical_problem_id": canonical_id,
            "canonical_record_id": f"record::{index}",
            "member_record_ids": [f"record::{index}"],
            "titles": [f"Problem {index}"],
            "alias_keys": [],
            "fronts": ["graphs_hypergraphs"],
            "statement_fingerprints": [],
            "identity_status": "singleton",
            "member_count": 1,
            "proof_claimed": False,
            "solution_claimed": False,
            "canonical_digest": f"digest-{index}",
        }
        rows.append(row)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _node(
    node_id: str,
    node_type: str,
    *,
    problem: str = "problem::alpha",
    metadata: dict | None = None,
    content: str | None = None,
) -> dict:
    return {
        "node_id": node_id,
        "node_type": node_type,
        "canonical_problem_id": problem,
        "title": node_id,
        "content": content or f"Content for {node_id}",
        "scope": "fixture scope",
        "source_refs": [f"fixture:{node_id}"],
        "observed_at": "2026-08-03T16:00:00Z",
        "metadata": metadata or {},
        "proof_claimed": False,
        "solution_claimed": False,
    }


def _edge(edge_id: str, source: str, target: str, relation: str, metadata: dict | None = None) -> dict:
    return {
        "edge_id": edge_id,
        "source_node_id": source,
        "target_node_id": target,
        "relation": relation,
        "scope": "fixture scope",
        "evidence_refs": [] if relation == "merely_mentions" else [f"fixture:{edge_id}"],
        "metadata": metadata or {},
    }


def _write_bundle(path: Path, nodes: list[dict], edges: list[dict], bundle_id: str = "bundle-fixture") -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "omega-problem-evidence-bundle/6",
                "bundle_id": bundle_id,
                "nodes": nodes,
                "edges": edges,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_kernel_checked_restricted_case_with_discharged_assumption_passes(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.restricted", "claim", metadata={"requested_status": "formal_restricted"}),
        _node("assumption.scope", "assumption"),
        _node(
            "formal.restricted",
            "formal_artifact",
            metadata={"proof_scope": "restricted", "kernel_checked": True, "verifier": "fixture-kernel"},
        ),
    ]
    edges = [
        _edge("edge.depends", "claim.restricted", "assumption.scope", "depends_on"),
        _edge("edge.discharges", "formal.restricted", "assumption.scope", "discharges"),
        _edge("edge.proves", "formal.restricted", "claim.restricted", "proves_restricted_case"),
    ]
    bundle = _write_bundle(tmp_path / "bundle.json", nodes, edges)
    output = tmp_path / "output"
    report = compile_evidence_graph(canonical, (bundle,), output)
    assessments = _read_jsonl(output / "claim_assessments.jsonl")

    assert report["promotion_allowed_count"] == 1
    assert assessments[0]["achieved_status"] == "formal_restricted"
    assert assessments[0]["promotion_allowed"] is True
    assert assessments[0]["blockers"] == []
    assert audit_evidence_graph(output)["valid"] is True


def test_numerical_evidence_cannot_promote_general_proof(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.general", "claim", metadata={"requested_status": "kernel_checked_general"}),
        _node("evidence.numeric", "evidence", metadata={"evidence_kind": "numerical"}),
    ]
    edges = [_edge("edge.supports", "evidence.numeric", "claim.general", "supports")]
    bundle = _write_bundle(tmp_path / "bundle.json", nodes, edges)
    output = tmp_path / "output"
    report = compile_evidence_graph(canonical, (bundle,), output)
    assessment = _read_jsonl(output / "claim_assessments.jsonl")[0]

    assert report["promotion_allowed_count"] == 0
    assert report["general_proof_from_numerical_evidence_count"] == 0
    assert assessment["achieved_status"] == "experimental"
    assert assessment["promotion_allowed"] is False
    assert "general_proof_from_numerical_evidence_forbidden" in assessment["blockers"]
    assert assessment["general_proof_from_numerical_evidence"] is False


def test_merely_mentions_does_not_support_claim(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.mentioned", "claim", metadata={"requested_status": "experimental"}),
        _node("evidence.paper", "evidence", metadata={"evidence_kind": "literature"}),
    ]
    edges = [_edge("edge.mentions", "evidence.paper", "claim.mentioned", "merely_mentions")]
    output = tmp_path / "output"
    compile_evidence_graph(canonical, (_write_bundle(tmp_path / "bundle.json", nodes, edges),), output)
    assessment = _read_jsonl(output / "claim_assessments.jsonl")[0]

    assert assessment["support_node_ids"] == []
    assert assessment["achieved_status"] == "candidate"
    assert assessment["promotion_allowed"] is False


def test_contradiction_blocks_claim_and_enters_mminus(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.refuted", "claim", metadata={"requested_status": "experimental"}),
        _node("counterexample.one", "counterexample", metadata={"independently_verified": True}),
    ]
    edges = [_edge("edge.contradicts", "counterexample.one", "claim.refuted", "contradicts")]
    output = tmp_path / "output"
    report = compile_evidence_graph(canonical, (_write_bundle(tmp_path / "bundle.json", nodes, edges),), output)
    assessment = _read_jsonl(output / "claim_assessments.jsonl")[0]
    mminus = _read_jsonl(output / "mminus_records.jsonl")

    assert report["contradiction_edge_count"] == 1
    assert assessment["promotion_allowed"] is False
    assert any(item.startswith("contradiction:") for item in assessment["blockers"])
    assert {row["reason_type"] for row in mminus} == {"counterexample", "contradicts"}
    assert all(row["immutable"] is True for row in mminus)


def test_undischarged_assumption_and_active_barrier_block_promotion(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.blocked", "claim", metadata={"requested_status": "candidate"}),
        _node("assumption.open", "assumption"),
        _node("barrier.known", "barrier"),
    ]
    edges = [
        _edge("edge.depends", "claim.blocked", "assumption.open", "depends_on"),
        _edge("edge.scopes", "barrier.known", "claim.blocked", "scopes"),
    ]
    output = tmp_path / "output"
    compile_evidence_graph(canonical, (_write_bundle(tmp_path / "bundle.json", nodes, edges),), output)
    assessment = _read_jsonl(output / "claim_assessments.jsonl")[0]

    assert "undischarged_assumption:assumption.open" in assessment["blockers"]
    assert "active_barrier:barrier.known" in assessment["blockers"]
    assert assessment["promotion_allowed"] is False


def test_cross_problem_support_edge_fails_closed(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl", ("problem::alpha", "problem::beta"))
    nodes = [
        _node("claim.alpha", "claim", problem="problem::alpha", metadata={"requested_status": "candidate"}),
        _node("evidence.beta", "evidence", problem="problem::beta", metadata={"evidence_kind": "numerical"}),
    ]
    edges = [_edge("edge.cross", "evidence.beta", "claim.alpha", "supports")]
    bundle = _write_bundle(tmp_path / "bundle.json", nodes, edges)
    with pytest.raises(ValueError, match="cross-problem edge"):
        compile_evidence_graph(canonical, (bundle,), tmp_path / "output")


def test_deterministic_materialization_and_tamper_detection(tmp_path: Path) -> None:
    canonical = _write_canonical(tmp_path / "canonical.jsonl")
    nodes = [
        _node("claim.test", "claim", metadata={"requested_status": "experimental"}),
        _node("evidence.test", "evidence", metadata={"evidence_kind": "numerical"}),
    ]
    edges = [_edge("edge.support", "evidence.test", "claim.test", "supports")]
    bundle = _write_bundle(tmp_path / "bundle.json", nodes, edges)
    first, second = tmp_path / "first", tmp_path / "second"
    report_a = compile_evidence_graph(canonical, (bundle,), first)
    report_b = compile_evidence_graph(canonical, (bundle,), second)

    assert report_a == report_b
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    assert audit_evidence_graph(first)["valid"] is True

    path = first / "nodes.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["title"] += " tampered"
    rows[0] = json.dumps(payload, sort_keys=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    audit = audit_evidence_graph(first)
    assert audit["valid"] is False
    assert any("nodes.jsonl: sha256 mismatch" in error for error in audit["errors"])
