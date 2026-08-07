from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r05 import (
    audit_identity_graph,
    compile_identity_graph,
    normalize_text,
    statement_fingerprint,
    structural_signature,
)


def _row(
    source: str,
    problem_id: str,
    title: str,
    statement: str | None,
    *,
    front: str = "graphs_hypergraphs",
    aliases: list[str] | None = None,
    provenance_character: str = "a",
) -> dict:
    return {
        "source_id": source,
        "problem_id": problem_id,
        "title": title,
        "front": front,
        "source_locator": f"{source}:{problem_id}",
        "source_verified_at": None,
        "statement": statement,
        "aliases": aliases or [],
        "status_receipt_id": f"receipt::{source}::{problem_id}",
        "adapter_provenance_digest": provenance_character * 64,
        "solution_claimed": False,
    }


def _record_id(source: str, problem_id: str, character: str) -> str:
    return f"record::{source}::{problem_id}::{character * 16}"


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_decisions(path: Path, decisions: list[dict]) -> Path:
    path.write_text(
        json.dumps({"schema": "omega-problem-identity-decisions/5", "decisions": decisions}, indent=2),
        encoding="utf-8",
    )
    return path


def test_unicode_normalization_and_structural_signatures() -> None:
    assert normalize_text("Erdős–Hajnal conjecture") == "erdős hajnal conjecture"
    statement = "For every finite graph, there exists an integer n such that P(n) holds."
    quantifiers, domains = structural_signature(statement)
    assert "forall" in quantifiers
    assert "exists" in quantifiers
    assert "graphs" in domains
    assert "integers" in domains
    assert statement_fingerprint(statement) == statement_fingerprint(statement)


def test_exact_statement_front_and_signature_merge_deterministically(tmp_path: Path) -> None:
    rows = [
        _row("source_a", "p1", "Graph parity conjecture", "For every finite graph, property P holds.", provenance_character="a"),
        _row("source_b", "p2", "Conjecture de parité", "For every finite graph, property P holds.", provenance_character="b"),
    ]
    imports_a = _write_jsonl(tmp_path / "a.jsonl", rows)
    imports_b = _write_jsonl(tmp_path / "b.jsonl", list(reversed(rows)))
    first, second = tmp_path / "first", tmp_path / "second"
    report_a = compile_identity_graph((imports_a,), first)
    report_b = compile_identity_graph((imports_b,), second)

    assert report_a == report_b
    assert report_a["source_record_count"] == 2
    assert report_a["canonical_problem_count"] == 1
    assert report_a["automatic_exact_statement_merge_edge_count"] == 1
    assert report_a["fuzzy_merge_count"] == 0
    assert audit_identity_graph(first)["valid"] is True
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_same_title_different_statement_is_quarantined_not_merged(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "Shared conjecture", "For every graph, property P holds.", provenance_character="a"),
        _row("source_b", "p2", "Shared conjecture", "There exists a graph with property Q.", provenance_character="b"),
    ])
    output = tmp_path / "output"
    report = compile_identity_graph((imports,), output)
    collisions = _read_jsonl(output / "collision_quarantine.jsonl")

    assert report["canonical_problem_count"] == 2
    assert report["title_only_merge_count"] == 0
    assert report["collision_quarantine_count"] == 1
    assert "different_statement_fingerprints" in collisions[0]["reason_codes"]
    assert audit_identity_graph(output)["valid"] is True


def test_fuzzy_title_similarity_only_creates_review_candidate(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "Graph parity conjecture", "For every graph, P holds.", provenance_character="a"),
        _row("source_b", "p2", "Graph parity problem", "There exists a graph where Q holds.", provenance_character="b"),
    ])
    output = tmp_path / "output"
    report = compile_identity_graph((imports,), output)
    candidates = _read_jsonl(output / "candidate_edges.jsonl")

    assert report["canonical_problem_count"] == 2
    assert report["fuzzy_candidate_count"] == 1
    assert report["fuzzy_merge_count"] == 0
    assert candidates[0]["identity_merge"] is False
    assert candidates[0]["requires_review"] is True


def test_manual_split_overrides_exact_statement_merge(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "Variant A", "For every graph, P holds.", provenance_character="a"),
        _row("source_b", "p2", "Variant B", "For every graph, P holds.", provenance_character="b"),
    ])
    decisions = _write_decisions(tmp_path / "decisions.json", [{
        "decision_id": "split-001",
        "action": "split",
        "record_ids": [_record_id("source_a", "p1", "a"), _record_id("source_b", "p2", "b")],
        "reason": "The source statements use the same prose but refer to distinct scoped objects.",
        "decided_by": "OAK-review-fixture",
        "decided_at": "2026-08-03T16:00:00Z",
        "evidence_refs": ["fixture:scope-a", "fixture:scope-b"],
    }])
    output = tmp_path / "output"
    report = compile_identity_graph((imports,), output, decision_paths=(decisions,))

    assert report["canonical_problem_count"] == 2
    assert report["automatic_exact_statement_merge_edge_count"] == 0
    assert report["decision_receipt_count"] == 1
    assert audit_identity_graph(output)["valid"] is True


def test_manual_merge_requires_receipt_and_preserves_canonical_choice(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "Historical name", "Statement form A.", provenance_character="a"),
        _row("source_b", "p2", "Modern name", "Equivalent statement form B.", provenance_character="b"),
    ])
    canonical = _record_id("source_b", "p2", "b")
    decisions = _write_decisions(tmp_path / "decisions.json", [{
        "decision_id": "merge-001",
        "action": "merge",
        "record_ids": [_record_id("source_a", "p1", "a"), canonical],
        "canonical_record_id": canonical,
        "reason": "A reviewed source proves the formulations equivalent.",
        "decided_by": "OAK-review-fixture",
        "decided_at": "2026-08-03T16:00:00Z",
        "evidence_refs": ["fixture:equivalence-proof"],
    }])
    output = tmp_path / "output"
    report = compile_identity_graph((imports,), output, decision_paths=(decisions,))
    canonical_rows = _read_jsonl(output / "canonical_problems.jsonl")

    assert report["canonical_problem_count"] == 1
    assert report["manual_merge_edge_count"] == 1
    assert canonical_rows[0]["canonical_record_id"] == canonical


def test_transitive_merge_cannot_bypass_split_receipt(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("s", "a", "A", "Statement A", provenance_character="a"),
        _row("s", "b", "B", "Statement B", provenance_character="b"),
        _row("s", "c", "C", "Statement C", provenance_character="c"),
    ])
    a, b, c = _record_id("s", "a", "a"), _record_id("s", "b", "b"), _record_id("s", "c", "c")
    decisions = _write_decisions(tmp_path / "decisions.json", [
        {
            "decision_id": "split-ac",
            "action": "split",
            "record_ids": [a, c],
            "reason": "A and C are explicitly distinct.",
            "decided_by": "OAK-review-fixture",
            "decided_at": "2026-08-03T16:00:00Z",
            "evidence_refs": ["fixture:split"],
        },
        {
            "decision_id": "merge-ab",
            "action": "merge",
            "record_ids": [a, b],
            "reason": "A and B are equivalent.",
            "decided_by": "OAK-review-fixture",
            "decided_at": "2026-08-03T16:01:00Z",
            "evidence_refs": ["fixture:ab"],
        },
        {
            "decision_id": "merge-bc",
            "action": "merge",
            "record_ids": [b, c],
            "reason": "B and C are claimed equivalent.",
            "decided_by": "OAK-review-fixture",
            "decided_at": "2026-08-03T16:02:00Z",
            "evidence_refs": ["fixture:bc"],
        },
    ])
    with pytest.raises(ValueError, match="transitively violates split"):
        compile_identity_graph((imports,), tmp_path / "output", decision_paths=(decisions,))


def test_declared_alias_does_not_merge_distinct_records(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "English title", "Statement A.", aliases=["Titre français"], provenance_character="a"),
        _row("source_b", "p2", "Titre français", "Statement B.", provenance_character="b"),
    ])
    output = tmp_path / "output"
    report = compile_identity_graph((imports,), output)
    aliases = _read_jsonl(output / "alias_edges.jsonl")

    assert report["canonical_problem_count"] == 2
    assert report["alias_edge_count"] == 1
    assert aliases[0]["identity_merge"] is False


def test_strict_audit_detects_tampering(tmp_path: Path) -> None:
    imports = _write_jsonl(tmp_path / "imports.jsonl", [
        _row("source_a", "p1", "Test problem", "For every graph, P holds.", provenance_character="a"),
    ])
    output = tmp_path / "output"
    compile_identity_graph((imports,), output)
    path = output / "source_records.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["title"] += " tampered"
    rows[0] = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    audit = audit_identity_graph(output)
    assert audit["valid"] is False
    assert any("source_records.jsonl: sha256 mismatch" in error for error in audit["errors"])
