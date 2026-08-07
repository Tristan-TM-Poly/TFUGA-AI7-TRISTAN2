from __future__ import annotations

import json
from pathlib import Path

from omega_millennium_t.r06 import audit_evidence_graph, compile_evidence_graph


def test_violated_assumption_is_not_treated_as_discharged(tmp_path: Path) -> None:
    canonical = {
        "canonical_problem_id": "problem::violation-fixture",
        "canonical_record_id": "record::violation-fixture",
        "member_record_ids": ["record::violation-fixture"],
        "titles": ["Violation fixture"],
        "alias_keys": [],
        "fronts": ["logic_foundations"],
        "statement_fingerprints": [],
        "identity_status": "singleton",
        "member_count": 1,
        "proof_claimed": False,
        "solution_claimed": False,
        "canonical_digest": "fixture-digest",
    }
    canonical_path = tmp_path / "canonical.jsonl"
    canonical_path.write_text(json.dumps(canonical) + "\n", encoding="utf-8")

    def node(node_id: str, node_type: str, metadata: dict) -> dict:
        return {
            "node_id": node_id,
            "node_type": node_type,
            "canonical_problem_id": "problem::violation-fixture",
            "title": node_id,
            "content": node_id,
            "scope": "fixture scope",
            "source_refs": [f"fixture:{node_id}"],
            "observed_at": "2026-08-03T16:00:00Z",
            "metadata": metadata,
            "proof_claimed": False,
            "solution_claimed": False,
        }

    bundle = {
        "schema": "omega-problem-evidence-bundle/6",
        "bundle_id": "violation-semantics-fixture",
        "nodes": [
            node("claim.one", "claim", {"requested_status": "candidate"}),
            node("assumption.one", "assumption", {}),
            node("evidence.violation", "evidence", {"evidence_kind": "numerical"}),
        ],
        "edges": [
            {
                "edge_id": "edge.depends",
                "source_node_id": "claim.one",
                "target_node_id": "assumption.one",
                "relation": "depends_on",
                "scope": "fixture scope",
                "evidence_refs": ["fixture:depends"],
                "metadata": {},
            },
            {
                "edge_id": "edge.violates",
                "source_node_id": "evidence.violation",
                "target_node_id": "assumption.one",
                "relation": "violates",
                "scope": "fixture scope",
                "evidence_refs": ["fixture:violation"],
                "metadata": {},
            },
        ],
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    output = tmp_path / "output"
    compile_evidence_graph(canonical_path, (bundle_path,), output)

    assessment = json.loads((output / "claim_assessments.jsonl").read_text(encoding="utf-8"))
    assert assessment["promotion_allowed"] is False
    assert "violated_assumption:assumption.one" in assessment["blockers"]
    assert "undischarged_assumption:assumption.one" not in assessment["blockers"]
    assert audit_evidence_graph(output)["valid"] is True
