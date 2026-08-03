"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.6."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

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


def compile_evidence_graph(
    canonical_problems_jsonl: str | Path,
    bundle_paths: Sequence[str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
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
        item for item in manifest["artifacts"]
        if item.get("path") != refs_path.name
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
        if manifest.get("canonical_identity_input_digest") != stable_digest(refs):
            errors.append("canonical identity input digest mismatch")
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        if report.get("canonical_identity_ref_count") != len(refs):
            errors.append("report canonical_identity_ref_count mismatch")
        if report.get("canonical_identity_input_digest") != stable_digest(refs):
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
