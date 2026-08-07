from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .compiler import assess_claims, build_mminus
from .model import EvidenceEdge, EvidenceNode, build_edge, file_receipt, read_jsonl, stable_digest


def audit_evidence_graph(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "bundle_receipts.jsonl",
        "nodes.jsonl",
        "edges.jsonl",
        "claim_assessments.jsonl",
        "mminus_records.jsonl",
        "evidence_graph.graphml",
        "manifest.json",
        "report.json",
    }
    missing = sorted(name for name in required if not (output / name).exists())
    if missing:
        return {
            "schema": "omega-problem-evidence-audit/6",
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

    bundles = read_jsonl(output / "bundle_receipts.jsonl")
    node_rows = read_jsonl(output / "nodes.jsonl")
    edge_rows = read_jsonl(output / "edges.jsonl")
    assessments = read_jsonl(output / "claim_assessments.jsonl")
    mminus = read_jsonl(output / "mminus_records.jsonl")

    nodes: dict[str, EvidenceNode] = {}
    for row in node_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "node_digest"})
        if row.get("node_digest") != expected:
            errors.append(f"{row.get('node_id')}: node digest mismatch")
        try:
            node = EvidenceNode(**row)
        except TypeError as exc:
            errors.append(f"{row.get('node_id')}: invalid node shape: {exc}")
            continue
        if node.node_id in nodes:
            errors.append(f"{node.node_id}: duplicate node")
        nodes[node.node_id] = node
        if node.solution_claimed:
            errors.append(f"{node.node_id}: solution claim forbidden")

    edges: list[EvidenceEdge] = []
    edge_ids: set[str] = set()
    for row in edge_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "edge_digest"})
        if row.get("edge_digest") != expected:
            errors.append(f"{row.get('edge_id')}: edge digest mismatch")
        try:
            rebuilt = build_edge({k: v for k, v in row.items() if k != "edge_digest"}, nodes)
            edge = EvidenceEdge(**row)
        except (TypeError, ValueError) as exc:
            errors.append(f"{row.get('edge_id')}: invalid edge: {exc}")
            continue
        if rebuilt.edge_digest != row.get("edge_digest"):
            errors.append(f"{row.get('edge_id')}: semantic rebuild digest mismatch")
        if edge.edge_id in edge_ids:
            errors.append(f"{edge.edge_id}: duplicate edge")
        edge_ids.add(edge.edge_id)
        edges.append(edge)

    recomputed_assessments = assess_claims(nodes, edges)
    if assessments != recomputed_assessments:
        errors.append("claim assessments do not match recomputation")
    for row in assessments:
        expected = stable_digest({k: v for k, v in row.items() if k != "assessment_digest"})
        if row.get("assessment_digest") != expected:
            errors.append(f"{row.get('claim_id')}: assessment digest mismatch")
        if row.get("general_proof_from_numerical_evidence") is not False:
            errors.append(f"{row.get('claim_id')}: numerical evidence promoted to general proof")
        if row.get("mathematical_truth_probability_claimed") is not False:
            errors.append(f"{row.get('claim_id')}: mathematical truth probability claimed")

    recomputed_mminus = build_mminus(nodes, edges)
    if mminus != recomputed_mminus:
        errors.append("M-minus records do not match recomputation")
    for row in mminus:
        expected = stable_digest({k: v for k, v in row.items() if k != "mminus_digest"})
        if row.get("mminus_digest") != expected:
            errors.append(f"{row.get('mminus_id')}: M-minus digest mismatch")
        if row.get("immutable") is not True:
            errors.append(f"{row.get('mminus_id')}: M-minus must be immutable")

    expected_counts = {
        "bundle_count": len(bundles),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "claim_count": sum(node.node_type == "claim" for node in nodes.values()),
        "assessment_count": len(assessments),
        "promotion_allowed_count": sum(row.get("promotion_allowed") is True for row in assessments),
        "blocked_claim_count": sum(row.get("promotion_allowed") is not True for row in assessments),
        "mminus_record_count": len(mminus),
        "contradiction_edge_count": sum(edge.relation == "contradicts" for edge in edges),
        "merely_mentions_edge_count": sum(edge.relation == "merely_mentions" for edge in edges),
    }
    for field, actual in expected_counts.items():
        if report.get(field) != actual:
            errors.append(f"report {field}: expected {actual}, got {report.get(field)}")

    if manifest.get("general_proof_from_numerical_evidence_allowed") is not False:
        errors.append("manifest must forbid general proof from numerical evidence")
    if manifest.get("mention_counts_as_support") is not False:
        errors.append("manifest must keep mentions distinct from support")
    if manifest.get("mminus_mutable") is not False:
        errors.append("manifest must keep M-minus immutable")
    if report.get("general_proof_from_numerical_evidence_count") != 0:
        errors.append("report contains numerical-to-general proof promotion")
    for field in ("mathematical_truth_probability_claimed", "solution_claimed", "scientific_validation_claimed"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")

    return {
        "schema": "omega-problem-evidence-audit/6",
        "valid": not errors,
        "errors": errors,
        "bundle_count": len(bundles),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "assessment_count": len(assessments),
        "mminus_record_count": len(mminus),
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
    }
