from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import all_pairs, file_receipt, read_jsonl, stable_digest


def audit_identity_graph(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "source_records.jsonl",
        "canonical_problems.jsonl",
        "identity_edges.jsonl",
        "alias_edges.jsonl",
        "candidate_edges.jsonl",
        "decision_receipts.jsonl",
        "collision_quarantine.jsonl",
        "identity_graph.graphml",
        "manifest.json",
        "report.json",
    }
    missing = sorted(name for name in required if not (output / name).exists())
    if missing:
        return {
            "schema": "omega-problem-identity-audit/5",
            "valid": False,
            "errors": [f"missing artifact: {name}" for name in missing],
            "solution_claimed": False,
        }

    errors: list[str] = []
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    if manifest.get("digest") != stable_digest({k: v for k, v in manifest.items() if k != "digest"}):
        errors.append("manifest digest mismatch")
    if report.get("digest") != stable_digest({k: v for k, v in report.items() if k != "digest"}):
        errors.append("report digest mismatch")

    manifest_artifacts = {item["path"]: item for item in manifest.get("artifacts", [])}
    for name in required - {"manifest.json", "report.json"}:
        expected = manifest_artifacts.get(name)
        if expected is None:
            errors.append(f"manifest missing {name}")
            continue
        actual = file_receipt(output / name)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected.get(field):
                errors.append(f"{name}: {field} mismatch")

    source_rows = read_jsonl(output / "source_records.jsonl")
    canonical_rows = read_jsonl(output / "canonical_problems.jsonl")
    identity_edges = read_jsonl(output / "identity_edges.jsonl")
    alias_edges = read_jsonl(output / "alias_edges.jsonl")
    candidate_edges = read_jsonl(output / "candidate_edges.jsonl")
    decisions = read_jsonl(output / "decision_receipts.jsonl")
    collisions = read_jsonl(output / "collision_quarantine.jsonl")

    source_ids = {row.get("record_id") for row in source_rows}
    canonical_ids = {row.get("canonical_problem_id") for row in canonical_rows}
    if len(source_ids) != len(source_rows):
        errors.append("duplicate source record id")
    if len(canonical_ids) != len(canonical_rows):
        errors.append("duplicate canonical problem id")

    for row in source_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "record_digest"})
        if row.get("record_digest") != expected:
            errors.append(f"{row.get('record_id')}: source record digest mismatch")

    membership: list[str] = []
    for row in canonical_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "canonical_digest"})
        if row.get("canonical_digest") != expected:
            errors.append(f"{row.get('canonical_problem_id')}: canonical digest mismatch")
        member_ids = row.get("member_record_ids", [])
        membership.extend(member_ids)
        if not member_ids:
            errors.append(f"{row.get('canonical_problem_id')}: empty membership")
        if any(item not in source_ids for item in member_ids):
            errors.append(f"{row.get('canonical_problem_id')}: unknown member record")
        if row.get("canonical_record_id") not in member_ids:
            errors.append(f"{row.get('canonical_problem_id')}: canonical record is not a member")
        if row.get("solution_claimed") is not False or row.get("proof_claimed") is not False:
            errors.append(f"{row.get('canonical_problem_id')}: forbidden claim")
    if sorted(membership) != sorted(source_ids):
        errors.append("source records must belong to exactly one canonical problem")

    split_pairs: set[tuple[str, str]] = set()
    decision_ids: set[str] = set()
    for row in decisions:
        expected = stable_digest({k: v for k, v in row.items() if k != "decision_digest"})
        if row.get("decision_digest") != expected:
            errors.append(f"{row.get('decision_id')}: decision digest mismatch")
        decision_id = row.get("decision_id")
        if decision_id in decision_ids:
            errors.append(f"{decision_id}: duplicate decision")
        decision_ids.add(decision_id)
        if row.get("action") == "split":
            split_pairs.update(all_pairs(sorted(row.get("record_ids", []))))

    for row in identity_edges:
        expected = stable_digest({k: v for k, v in row.items() if k != "edge_digest"})
        if row.get("edge_digest") != expected:
            errors.append(f"{row.get('edge_id')}: identity edge digest mismatch")
        left, right = row.get("left_record_id"), row.get("right_record_id")
        if left not in source_ids or right not in source_ids:
            errors.append(f"{row.get('edge_id')}: unknown source record")
        if tuple(sorted((str(left), str(right)))) in split_pairs:
            errors.append(f"{row.get('edge_id')}: split decision violated")
        if row.get("merge_basis") not in {
            "manual_evidence_receipt",
            "exact_statement_front_and_signature",
        }:
            errors.append(f"{row.get('edge_id')}: forbidden merge basis")

    for row in alias_edges:
        expected = stable_digest({k: v for k, v in row.items() if k != "edge_digest"})
        if row.get("edge_digest") != expected:
            errors.append(f"{row.get('edge_id')}: alias edge digest mismatch")
        if row.get("record_id") not in source_ids:
            errors.append(f"{row.get('edge_id')}: unknown alias source record")
        if row.get("canonical_problem_id") not in canonical_ids:
            errors.append(f"{row.get('edge_id')}: unknown alias canonical problem")
        if row.get("identity_merge") is not False:
            errors.append(f"{row.get('edge_id')}: alias edge cannot merge identity")

    for row in candidate_edges:
        expected = stable_digest({k: v for k, v in row.items() if k != "edge_digest"})
        if row.get("edge_digest") != expected:
            errors.append(f"{row.get('edge_id')}: candidate edge digest mismatch")
        if row.get("left_record_id") not in source_ids or row.get("right_record_id") not in source_ids:
            errors.append(f"{row.get('edge_id')}: unknown candidate source record")
        if row.get("identity_merge") is not False:
            errors.append(f"{row.get('edge_id')}: candidate edge cannot merge identity")
        if row.get("requires_review") is not True:
            errors.append(f"{row.get('edge_id')}: candidate edge must require review")
        similarity = row.get("similarity")
        if not isinstance(similarity, (int, float)) or not 0 <= similarity <= 1:
            errors.append(f"{row.get('edge_id')}: invalid similarity")

    for row in collisions:
        expected = stable_digest({k: v for k, v in row.items() if k != "collision_digest"})
        if row.get("collision_digest") != expected:
            errors.append(f"{row.get('collision_id')}: collision digest mismatch")
        if row.get("review_required") is not True:
            errors.append(f"{row.get('collision_id')}: collision must require review")
        if any(item not in source_ids for item in row.get("record_ids", [])):
            errors.append(f"{row.get('collision_id')}: unknown collision record")

    expected_counts = {
        "source_record_count": len(source_rows),
        "canonical_problem_count": len(canonical_rows),
        "alias_edge_count": len(alias_edges),
        "fuzzy_candidate_count": len(candidate_edges),
        "decision_receipt_count": len(decisions),
        "collision_quarantine_count": len(collisions),
        "automatic_exact_statement_merge_edge_count": sum(
            row.get("merge_basis") == "exact_statement_front_and_signature" for row in identity_edges
        ),
        "manual_merge_edge_count": sum(
            row.get("merge_basis") == "manual_evidence_receipt" for row in identity_edges
        ),
        "singleton_count": sum(row.get("identity_status") == "singleton" for row in canonical_rows),
        "merged_problem_count": sum(row.get("identity_status") == "merged" for row in canonical_rows),
    }
    for field, actual in expected_counts.items():
        if report.get(field) != actual:
            errors.append(f"report {field}: expected {actual}, got {report.get(field)}")

    if report.get("fuzzy_merge_count") != 0 or manifest.get("fuzzy_merge_allowed") is not False:
        errors.append("fuzzy merges must remain disabled")
    if report.get("title_only_merge_count") != 0 or manifest.get("title_only_merge_allowed") is not False:
        errors.append("title-only merges must remain disabled")
    for field in ("solution_claimed", "formal_proof_claimed", "scientific_validation_claimed"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")

    return {
        "schema": "omega-problem-identity-audit/5",
        "valid": not errors,
        "errors": errors,
        "source_record_count": len(source_rows),
        "canonical_problem_count": len(canonical_rows),
        "identity_edge_count": len(identity_edges),
        "alias_edge_count": len(alias_edges),
        "fuzzy_candidate_count": len(candidate_edges),
        "collision_quarantine_count": len(collisions),
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
    }
