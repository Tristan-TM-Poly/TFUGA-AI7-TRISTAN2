"""Public and hardened API for Ω-PROBLEM-ATLAS-T∞ R0.5."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from .audit import audit_identity_graph as _audit_identity_graph
from .compiler import compile_identity_graph as _compile_identity_graph
from .model import (
    DECISION_SCHEMA,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    all_pairs,
    normalize_statement,
    normalize_text,
    read_jsonl,
    statement_fingerprint,
    structural_signature,
)


def _validate_decision_evidence(decision_paths: Sequence[str | Path]) -> None:
    for path_like in decision_paths:
        path = Path(path_like)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != DECISION_SCHEMA:
            raise ValueError(f"{path}: unsupported decision schema")
        for decision in payload.get("decisions", []):
            evidence = decision.get("evidence_refs") if isinstance(decision, dict) else None
            if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
                decision_id = decision.get("decision_id", "unknown") if isinstance(decision, dict) else "unknown"
                raise ValueError(f"{path}: {decision_id} requires at least one evidence reference")


def compile_identity_graph(
    import_paths: Sequence[str | Path],
    output_dir: str | Path,
    *,
    decision_paths: Sequence[str | Path] = (),
) -> dict[str, Any]:
    _validate_decision_evidence(decision_paths)
    return _compile_identity_graph(import_paths, output_dir, decision_paths=decision_paths)


def audit_identity_graph(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    result = _audit_identity_graph(output)
    errors = list(result.get("errors", []))
    decisions_path = output / "decision_receipts.jsonl"
    canonical_path = output / "canonical_problems.jsonl"
    if decisions_path.exists() and canonical_path.exists():
        decisions = read_jsonl(decisions_path)
        split_pairs: set[tuple[str, str]] = set()
        for decision in decisions:
            evidence = decision.get("evidence_refs")
            if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
                errors.append(f"{decision.get('decision_id')}: missing evidence reference")
            if decision.get("action") == "split":
                split_pairs.update(all_pairs(sorted(decision.get("record_ids", []))))
        for canonical in read_jsonl(canonical_path):
            members = sorted(canonical.get("member_record_ids", []))
            violations = sorted(all_pairs(members) & split_pairs)
            if violations:
                errors.append(
                    f"{canonical.get('canonical_problem_id')}: canonical membership violates split receipts {violations}"
                )
    result["errors"] = errors
    result["valid"] = not errors
    return result


__all__ = [
    "DECISION_SCHEMA",
    "MANIFEST_SCHEMA",
    "REPORT_SCHEMA",
    "audit_identity_graph",
    "compile_identity_graph",
    "normalize_statement",
    "normalize_text",
    "statement_fingerprint",
    "structural_signature",
]
