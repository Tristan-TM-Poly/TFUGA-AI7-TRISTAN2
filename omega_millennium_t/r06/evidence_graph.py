"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.6."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .audit import audit_evidence_graph as _audit_evidence_graph
from .compiler import compile_evidence_graph as _compile_evidence_graph
from .model import (
    BUNDLE_SCHEMA,
    NODE_TYPES,
    RELATIONS,
    file_receipt,
    read_jsonl,
    stable_digest,
    write_jsonl,
)

EVIDENTIAL_SOURCES = {
    "evidence",
    "counterexample",
    "computation_receipt",
    "formal_artifact",
    "independent_review",
}


def _validate_bundle_semantics(bundle_paths: Sequence[str | Path]) -> None:
    for path_like in bundle_paths:
        path = Path(path_like)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != BUNDLE_SCHEMA:
            raise ValueError(f"{path}: unsupported bundle schema")
        raw_nodes = payload.get("nodes", [])
        raw_edges = payload.get("edges", [])
        if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
            raise ValueError(f"{path}: nodes and edges must be lists")
        node_types: dict[str, str] = {}
        for raw in raw_nodes:
            if not isinstance(raw, Mapping):
                raise ValueError(f"{path}: node must be an object")
            node_id = str(raw.get("node_id", ""))
            node_type = str(raw.get("node_type", ""))
            metadata = raw.get("metadata", {})
            node_types[node_id] = node_type
            if not isinstance(metadata, Mapping):
                raise ValueError(f"{path}: {node_id} metadata must be an object")
            if node_type == "computation_receipt":
                if metadata.get("outcome") not in {
                    "success", "failure", "timeout", "invalid_certificate", "diverged"
                }:
                    raise ValueError(f"{path}: {node_id} requires a valid computation outcome")
                if not str(metadata.get("run_digest", "")).strip():
                    raise ValueError(f"{path}: {node_id} requires run_digest")
                if "certificate_verified" in metadata and not isinstance(metadata["certificate_verified"], bool):
                    raise ValueError(f"{path}: {node_id} certificate_verified must be boolean")
            elif node_type == "formal_artifact":
                if metadata.get("kernel_checked") is True and not str(metadata.get("verifier", "")).strip():
                    raise ValueError(f"{path}: {node_id} kernel-checked artifact requires verifier")
            elif node_type == "independent_review":
                if not str(metadata.get("reviewer", "")).strip():
                    raise ValueError(f"{path}: {node_id} requires reviewer")
                if not str(metadata.get("review_scope", "")).strip():
                    raise ValueError(f"{path}: {node_id} requires review_scope")
            elif node_type == "counterexample":
                if metadata.get("counterexample_scope") not in {"restricted", "general"}:
                    raise ValueError(f"{path}: {node_id} requires counterexample_scope")
                if "independently_verified" in metadata and not isinstance(metadata["independently_verified"], bool):
                    raise ValueError(f"{path}: {node_id} independently_verified must be boolean")
        for raw in raw_edges:
            if not isinstance(raw, Mapping):
                raise ValueError(f"{path}: edge must be an object")
            edge_id = str(raw.get("edge_id", ""))
            source_type = node_types.get(str(raw.get("source_node_id", "")))
            target_type = node_types.get(str(raw.get("target_node_id", "")))
            relation = str(raw.get("relation", ""))
            if relation in {"supports", "improves_bound"} and source_type not in EVIDENTIAL_SOURCES:
                raise ValueError(f"{path}: {edge_id} has non-evidential source")
            if relation == "proves_restricted_case" and source_type not in {"evidence", "formal_artifact"}:
                raise ValueError(f"{path}: {edge_id} has invalid restricted-proof source")
            if relation == "contradicts" and source_type not in EVIDENTIAL_SOURCES:
                raise ValueError(f"{path}: {edge_id} has invalid contradiction source")
            if relation in {"discharges", "violates"} and source_type not in EVIDENTIAL_SOURCES:
                raise ValueError(f"{path}: {edge_id} has invalid discharge/violation source")
            if relation == "scopes" and target_type != "claim":
                raise ValueError(f"{path}: {edge_id} scopes must target a claim")


def compile_evidence_graph(
    canonical_problems_jsonl: str | Path,
    bundle_paths: Sequence[str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
    _validate_bundle_semantics(bundle_paths)
    canonical_path = Path(canonical_problems_jsonl)
    output = Path(output_dir)
    report = _compile_evidence_graph(canonical_path, bundle_paths, output)

    canonical_rows = read_jsonl(canonical_path)
    refs: list[dict[str, Any]] = []
    for row in canonical_rows:
        ref = {
            "canonical_problem_id": row["canonical_problem_id"],
            "canonical_digest": row.get("canonical_digest"),
            "member_count": row.get("member_count"),
        }
        ref["identity_ref_digest"] = stable_digest(ref)
        refs.append(ref)
    refs.sort(key=lambda row: row["canonical_problem_id"])
    refs_path = output / "canonical_identity_refs.jsonl"
    write_jsonl(refs_path, refs)

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"] = [
        item for item in manifest["artifacts"] if item.get("path") != refs_path.name
    ] + [file_receipt(refs_path)]
    manifest["artifacts"].sort(key=lambda item: item["path"])
    manifest["canonical_identity_input_digest"] = stable_digest(refs)
    manifest["digest"] = stable_digest({k: v for k, v in manifest.items() if k != "digest"})
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report_path = output / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["canonical_identity_ref_count"] = len(refs)
    report["canonical_identity_input_digest"] = manifest["canonical_identity_input_digest"]
    report["manifest_digest"] = manifest["digest"]
    report["digest"] = stable_digest({k: v for k, v in report.items() if k != "digest"})
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def audit_evidence_graph(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    result = _audit_evidence_graph(output)
    errors = list(result.get("errors", []))
    refs_path = output / "canonical_identity_refs.jsonl"
    if not refs_path.exists():
        errors.append("missing artifact: canonical_identity_refs.jsonl")
    else:
        refs = read_jsonl(refs_path)
        ref_ids: set[str] = set()
        for row in refs:
            expected = stable_digest({k: v for k, v in row.items() if k != "identity_ref_digest"})
            if row.get("identity_ref_digest") != expected:
                errors.append(f"{row.get('canonical_problem_id')}: identity reference digest mismatch")
            canonical_id = row.get("canonical_problem_id")
            if canonical_id in ref_ids:
                errors.append(f"{canonical_id}: duplicate identity reference")
            ref_ids.add(canonical_id)
        node_ids = {row.get("canonical_problem_id") for row in read_jsonl(output / "nodes.jsonl")}
        if not node_ids <= ref_ids:
            errors.append(f"nodes reference unknown canonical identities: {sorted(node_ids - ref_ids)}")
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        expected_receipt = next(
            (item for item in manifest.get("artifacts", []) if item.get("path") == refs_path.name),
            None,
        )
        if expected_receipt is None:
            errors.append("manifest missing canonical_identity_refs.jsonl")
        else:
            actual = file_receipt(refs_path)
            for field in ("sha256", "bytes", "rows"):
                if actual[field] != expected_receipt.get(field):
                    errors.append(f"canonical_identity_refs.jsonl: {field} mismatch")
        identity_digest = stable_digest(refs)
        if manifest.get("canonical_identity_input_digest") != identity_digest:
            errors.append("canonical identity input digest mismatch")
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        if report.get("canonical_identity_ref_count") != len(refs):
            errors.append("report canonical_identity_ref_count mismatch")
        if report.get("canonical_problem_count") != len(refs):
            errors.append("report canonical_problem_count mismatch")
        if report.get("canonical_identity_input_digest") != identity_digest:
            errors.append("report canonical_identity_input_digest mismatch")
        if report.get("manifest_digest") != manifest.get("digest"):
            errors.append("report manifest digest mismatch")
    result["errors"] = errors
    result["valid"] = not errors
    return result


__all__ = [
    "BUNDLE_SCHEMA",
    "NODE_TYPES",
    "RELATIONS",
    "audit_evidence_graph",
    "compile_evidence_graph",
]
