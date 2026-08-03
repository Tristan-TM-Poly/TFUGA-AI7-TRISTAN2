from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r05 import audit_identity_graph, compile_identity_graph
from omega_millennium_t.r05.model import stable_digest


def _write_imports(path: Path) -> tuple[Path, str, str]:
    rows = [
        {
            "source_id": "source_a",
            "problem_id": "p1",
            "title": "Variant A",
            "front": "graphs_hypergraphs",
            "source_locator": "source_a:p1",
            "source_verified_at": None,
            "statement": "For every graph, P holds.",
            "aliases": [],
            "status_receipt_id": "receipt::a",
            "adapter_provenance_digest": "a" * 64,
            "solution_claimed": False,
        },
        {
            "source_id": "source_b",
            "problem_id": "p2",
            "title": "Variant B",
            "front": "graphs_hypergraphs",
            "source_locator": "source_b:p2",
            "source_verified_at": None,
            "statement": "For every graph, P holds.",
            "aliases": [],
            "status_receipt_id": "receipt::b",
            "adapter_provenance_digest": "b" * 64,
            "solution_claimed": False,
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path, "record::source_a::p1::aaaaaaaaaaaaaaaa", "record::source_b::p2::bbbbbbbbbbbbbbbb"


def _write_decisions(path: Path, left: str, right: str, evidence: list[str]) -> Path:
    payload = {
        "schema": "omega-problem-identity-decisions/5",
        "decisions": [
            {
                "decision_id": "split-001",
                "action": "split",
                "record_ids": [left, right],
                "reason": "Reviewed scope distinction.",
                "decided_by": "OAK-review-fixture",
                "decided_at": "2026-08-03T16:00:00Z",
                "evidence_refs": evidence,
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_decision_without_evidence_is_rejected(tmp_path: Path) -> None:
    imports, left, right = _write_imports(tmp_path / "imports.jsonl")
    decisions = _write_decisions(tmp_path / "decisions.json", left, right, [])
    with pytest.raises(ValueError, match="requires at least one evidence reference"):
        compile_identity_graph((imports,), tmp_path / "output", decision_paths=(decisions,))


def test_audit_detects_split_violation_in_canonical_membership(tmp_path: Path) -> None:
    imports, left, right = _write_imports(tmp_path / "imports.jsonl")
    decisions = _write_decisions(tmp_path / "decisions.json", left, right, ["fixture:scope-review"])
    output = tmp_path / "output"
    compile_identity_graph((imports,), output, decision_paths=(decisions,))

    canonical_path = output / "canonical_problems.jsonl"
    rows = [json.loads(line) for line in canonical_path.read_text(encoding="utf-8").splitlines()]
    forged = dict(rows[0])
    forged["member_record_ids"] = [left, right]
    forged["member_count"] = 2
    forged["identity_status"] = "merged"
    forged["canonical_record_id"] = left
    forged["canonical_digest"] = stable_digest({k: v for k, v in forged.items() if k != "canonical_digest"})
    canonical_path.write_text(json.dumps(forged, sort_keys=True) + "\n", encoding="utf-8")

    audit = audit_identity_graph(output)
    assert audit["valid"] is False
    assert any("canonical membership violates split receipts" in error for error in audit["errors"])
