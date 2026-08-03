from __future__ import annotations

from dataclasses import asdict
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    BUNDLE_SCHEMA,
    MANIFEST_SCHEMA,
    PROMOTION_RANK,
    REPORT_SCHEMA,
    EvidenceEdge,
    EvidenceNode,
    build_edge,
    build_node,
    file_receipt,
    read_jsonl,
    stable_digest,
    write_jsonl,
)

SUPPORT_RELATIONS = {"supports", "proves_restricted_case", "improves_bound", "reproduces"}
NEGATIVE_COMPUTATION_OUTCOMES = {"failure", "timeout", "invalid_certificate", "diverged"}


def _read_canonical_ids(path: Path) -> set[str]:
    rows = read_jsonl(path)
    ids = {str(row.get("canonical_problem_id", "")) for row in rows}
    if "" in ids or len(ids) != len(rows):
        raise ValueError("canonical problem file has blank or duplicate identifiers")
    return ids


def _load_bundles(paths: Sequence[str | Path]) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], list[dict[str, Any]]]:
    raw_nodes: list[Mapping[str, Any]] = []
    raw_edges: list[Mapping[str, Any]] = []
    bundle_receipts: list[dict[str, Any]] = []
    bundle_ids: set[str] = set()
    for path in sorted((Path(item) for item in paths), key=str):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != BUNDLE_SCHEMA:
            raise ValueError(f"{path}: unsupported bundle schema")
        bundle_id = str(payload.get("bundle_id", "")).strip()
        if not bundle_id or bundle_id in bundle_ids:
            raise ValueError(f"{path}: blank or duplicate bundle_id")
        bundle_ids.add(bundle_id)
        nodes = payload.get("nodes")
        edges = payload.get("edges")
        if not isinstance(nodes, list) or not all(isinstance(item, Mapping) for item in nodes):
            raise ValueError(f"{path}: nodes must be an object list")
        if not isinstance(edges, list) or not all(isinstance(item, Mapping) for item in edges):
            raise ValueError(f"{path}: edges must be an object list")
        raw_nodes.extend(nodes)
        raw_edges.extend(edges)
        bundle_receipts.append({
            "bundle_id": bundle_id,
            "source_path": path.name,
            "bundle_digest": stable_digest(payload),
            "node_count": len(nodes),
            "edge_count": len(edges),
        })
    return raw_nodes, raw_edges, sorted(bundle_receipts, key=lambda row: row["bundle_id"])


def assess_claims(nodes: Mapping[str, EvidenceNode], edges: Sequence[EvidenceEdge]) -> list[dict[str, Any]]:
    incoming: dict[str, list[EvidenceEdge]] = {node_id: [] for node_id in nodes}
    outgoing: dict[str, list[EvidenceEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        incoming[edge.target_node_id].append(edge)
        outgoing[edge.source_node_id].append(edge)

    discharged = {
        edge.target_node_id
        for edge in edges
        if edge.relation in {"discharges", "violates"}
    }
    assessments: list[dict[str, Any]] = []
    for claim in sorted((node for node in nodes.values() if node.node_type == "claim"), key=lambda item: item.node_id):
        requested = str(claim.metadata.get("requested_status", "candidate"))
        achieved = "candidate"
        blockers: list[str] = []
        support_ids: list[str] = []
        contradiction_ids: list[str] = []
        numerical_support = False
        exact_certificate = False
        restricted_formal = False
        general_formal_candidate = False
        kernel_checked_general = False
        accepted_review = False

        dependencies = [edge.target_node_id for edge in outgoing[claim.node_id] if edge.relation == "depends_on"]
        for assumption_id in dependencies:
            if assumption_id not in discharged:
                blockers.append(f"undischarged_assumption:{assumption_id}")

        scoped_barriers = [
            edge.source_node_id
            for edge in incoming[claim.node_id]
            if edge.relation == "scopes" and nodes[edge.source_node_id].node_type == "barrier"
        ]
        for barrier_id in scoped_barriers:
            if barrier_id not in discharged:
                blockers.append(f"active_barrier:{barrier_id}")

        for edge in incoming[claim.node_id]:
            source = nodes[edge.source_node_id]
            if edge.relation == "contradicts":
                contradiction_ids.append(source.node_id)
                blockers.append(f"contradiction:{source.node_id}")
                continue
            if edge.relation not in SUPPORT_RELATIONS:
                continue
            support_ids.append(source.node_id)
            if source.node_type == "evidence":
                kind = str(source.metadata.get("evidence_kind", ""))
                if kind in {"numerical", "symbolic", "experiment", "literature", "proof_text"}:
                    numerical_support = numerical_support or kind in {"numerical", "symbolic", "experiment"}
                    achieved = max((achieved, "experimental"), key=PROMOTION_RANK.get)
                if kind == "exact_computation" and source.metadata.get("certificate_verified") is True:
                    exact_certificate = True
                    achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)
            elif source.node_type == "computation_receipt":
                achieved = max((achieved, "experimental"), key=PROMOTION_RANK.get)
                if source.metadata.get("certificate_verified") is True:
                    exact_certificate = True
                    achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)
            elif source.node_type == "formal_artifact":
                scope = str(source.metadata.get("proof_scope", ""))
                checked = source.metadata.get("kernel_checked") is True
                if scope == "restricted" and checked:
                    restricted_formal = True
                    achieved = max((achieved, "formal_restricted"), key=PROMOTION_RANK.get)
                elif scope == "general" and checked:
                    kernel_checked_general = True
                    achieved = max((achieved, "kernel_checked_general"), key=PROMOTION_RANK.get)
                elif scope == "general":
                    general_formal_candidate = True
                    achieved = max((achieved, "general_proof_candidate"), key=PROMOTION_RANK.get)
            elif source.node_type == "independent_review":
                outcome = str(source.metadata.get("outcome", ""))
                if outcome == "accepted":
                    accepted_review = True
                elif outcome in {"challenged", "rejected"}:
                    blockers.append(f"review_{outcome}:{source.node_id}")

        if kernel_checked_general and accepted_review:
            achieved = "independently_reviewed_general"
        elif restricted_formal:
            achieved = max((achieved, "formal_restricted"), key=PROMOTION_RANK.get)
        elif exact_certificate:
            achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)

        if PROMOTION_RANK[requested] >= PROMOTION_RANK["general_proof_candidate"]:
            if not (general_formal_candidate or kernel_checked_general):
                blockers.append("general_status_requires_general_formal_artifact")
            if numerical_support and not (general_formal_candidate or kernel_checked_general):
                blockers.append("general_proof_from_numerical_evidence_forbidden")
        if PROMOTION_RANK[achieved] < PROMOTION_RANK[requested]:
            blockers.append(f"insufficient_evidence:{achieved}<{requested}")

        blockers = sorted(set(blockers))
        row = {
            "claim_id": claim.node_id,
            "canonical_problem_id": claim.canonical_problem_id,
            "requested_status": requested,
            "achieved_status": achieved,
            "promotion_allowed": not blockers and PROMOTION_RANK[achieved] >= PROMOTION_RANK[requested],
            "support_node_ids": sorted(set(support_ids)),
            "contradiction_node_ids": sorted(set(contradiction_ids)),
            "dependency_assumption_ids": sorted(set(dependencies)),
            "scoped_barrier_ids": sorted(set(scoped_barriers)),
            "blockers": blockers,
            "mathematical_truth_probability_claimed": False,
            "general_proof_from_numerical_evidence": False,
        }
        row["assessment_digest"] = stable_digest(row)
        assessments.append(row)
    return assessments


def build_mminus(nodes: Mapping[str, EvidenceNode], edges: Sequence[EvidenceEdge]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in sorted(nodes.values(), key=lambda item: item.node_id):
        reason: str | None = None
        if node.node_type == "barrier":
            reason = "barrier"
        elif node.node_type == "counterexample":
            reason = "counterexample"
        elif node.node_type == "computation_receipt" and node.metadata.get("outcome") in NEGATIVE_COMPUTATION_OUTCOMES:
            reason = f"computation_{node.metadata.get('outcome')}"
        elif node.node_type == "independent_review" and node.metadata.get("outcome") in {"challenged", "rejected"}:
            reason = f"review_{node.metadata.get('outcome')}"
        if reason:
            row = {
                "mminus_id": f"mminus::node::{node.node_id}",
                "canonical_problem_id": node.canonical_problem_id,
                "source_kind": "node",
                "source_id": node.node_id,
                "reason_type": reason,
                "immutable": True,
            }
            row["mminus_digest"] = stable_digest(row)
            rows.append(row)
    for edge in sorted(edges, key=lambda item: item.edge_id):
        if edge.relation not in {"contradicts", "violates"}:
            continue
        source = nodes[edge.source_node_id]
        row = {
            "mminus_id": f"mminus::edge::{edge.edge_id}",
            "canonical_problem_id": source.canonical_problem_id,
            "source_kind": "edge",
            "source_id": edge.edge_id,
            "reason_type": edge.relation,
            "immutable": True,
        }
        row["mminus_digest"] = stable_digest(row)
        rows.append(row)
    return rows


def _write_graphml(path: Path, nodes: Sequence[EvidenceNode], edges: Sequence[EvidenceEdge]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '<key id="label" for="node" attr.name="label" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<graph id="omega-problem-evidence-r06" edgedefault="directed">',
    ]
    for node in nodes:
        lines.append(
            f'<node id="{escape(node.node_id)}"><data key="kind">{escape(node.node_type)}</data>'
            f'<data key="label">{escape(node.title)}</data></node>'
        )
    for edge in edges:
        lines.append(
            f'<edge id="{escape(edge.edge_id)}" source="{escape(edge.source_node_id)}" '
            f'target="{escape(edge.target_node_id)}"><data key="relation">'
            f'{escape(edge.relation)}</data></edge>'
        )
    lines.extend(["</graph>", "</graphml>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_evidence_graph(
    canonical_problems_jsonl: str | Path,
    bundle_paths: Sequence[str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    canonical_ids = _read_canonical_ids(Path(canonical_problems_jsonl))
    raw_nodes, raw_edges, bundle_receipts = _load_bundles(bundle_paths)

    nodes_list = [build_node(raw, canonical_ids) for raw in raw_nodes]
    nodes_list.sort(key=lambda item: item.node_id)
    if len({node.node_id for node in nodes_list}) != len(nodes_list):
        raise ValueError("duplicate node_id")
    nodes = {node.node_id: node for node in nodes_list}
    edges = [build_edge(raw, nodes) for raw in raw_edges]
    edges.sort(key=lambda item: item.edge_id)
    if len({edge.edge_id for edge in edges}) != len(edges):
        raise ValueError("duplicate edge_id")

    assessments = assess_claims(nodes, edges)
    mminus = build_mminus(nodes, edges)
    node_rows = [asdict(node) for node in nodes_list]
    edge_rows = [asdict(edge) for edge in edges]

    write_jsonl(output / "bundle_receipts.jsonl", bundle_receipts)
    write_jsonl(output / "nodes.jsonl", node_rows)
    write_jsonl(output / "edges.jsonl", edge_rows)
    write_jsonl(output / "claim_assessments.jsonl", assessments)
    write_jsonl(output / "mminus_records.jsonl", mminus)
    _write_graphml(output / "evidence_graph.graphml", nodes_list, edges)

    artifact_names = (
        "bundle_receipts.jsonl",
        "nodes.jsonl",
        "edges.jsonl",
        "claim_assessments.jsonl",
        "mminus_records.jsonl",
        "evidence_graph.graphml",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifacts": [file_receipt(output / name) for name in artifact_names],
        "general_proof_from_numerical_evidence_allowed": False,
        "mention_counts_as_support": False,
        "mminus_mutable": False,
        "permanent_total_cap": None,
        "solution_claimed": False,
    }
    manifest["digest"] = stable_digest({k: v for k, v in manifest.items() if k != "digest"})
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": REPORT_SCHEMA,
        "status": "CERTIFIED_CLAIM_EVIDENCE_FIXTURE_R0_6",
        "canonical_problem_count": len(canonical_ids),
        "bundle_count": len(bundle_receipts),
        "node_count": len(nodes_list),
        "edge_count": len(edges),
        "claim_count": sum(node.node_type == "claim" for node in nodes_list),
        "assessment_count": len(assessments),
        "promotion_allowed_count": sum(row["promotion_allowed"] for row in assessments),
        "blocked_claim_count": sum(not row["promotion_allowed"] for row in assessments),
        "mminus_record_count": len(mminus),
        "contradiction_edge_count": sum(edge.relation == "contradicts" for edge in edges),
        "merely_mentions_edge_count": sum(edge.relation == "merely_mentions" for edge in edges),
        "general_proof_from_numerical_evidence_count": 0,
        "mathematical_truth_probability_claimed": False,
        "solution_claimed": False,
        "scientific_validation_claimed": False,
        "permanent_total_cap": None,
        "manifest_digest": manifest["digest"],
    }
    report["digest"] = stable_digest({k: v for k, v in report.items() if k != "digest"})
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
