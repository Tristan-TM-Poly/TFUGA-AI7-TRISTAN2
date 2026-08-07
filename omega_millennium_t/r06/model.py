from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

BUNDLE_SCHEMA = "omega-problem-evidence-bundle/6"
REPORT_SCHEMA = "omega-problem-evidence-report/6"
MANIFEST_SCHEMA = "omega-problem-evidence-manifest/6"

NODE_TYPES = {
    "claim",
    "evidence",
    "assumption",
    "barrier",
    "counterexample",
    "computation_receipt",
    "formal_artifact",
    "independent_review",
}

RELATIONS = {
    "supports",
    "contradicts",
    "scopes",
    "specializes",
    "generalizes",
    "depends_on",
    "discharges",
    "violates",
    "proves_restricted_case",
    "improves_bound",
    "reproduces",
    "merely_mentions",
}

PROMOTION_LEVELS = (
    "candidate",
    "experimental",
    "restricted_result",
    "formal_restricted",
    "general_proof_candidate",
    "kernel_checked_general",
    "independently_reviewed_general",
)
PROMOTION_RANK = {name: index for index, name in enumerate(PROMOTION_LEVELS)}

EVIDENCE_KINDS = {
    "numerical",
    "symbolic",
    "exact_computation",
    "experiment",
    "literature",
    "proof_text",
}


@dataclass(frozen=True)
class EvidenceNode:
    node_id: str
    node_type: str
    canonical_problem_id: str
    title: str
    content: str
    scope: str
    source_refs: tuple[str, ...]
    observed_at: str
    metadata: Mapping[str, Any]
    proof_claimed: bool
    solution_claimed: bool
    node_digest: str


@dataclass(frozen=True)
class EvidenceEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation: str
    scope: str
    evidence_refs: tuple[str, ...]
    metadata: Mapping[str, Any]
    edge_digest: str


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def parse_iso8601(value: str, field_name: str) -> str:
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} requires timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: row must be an object")
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "rows": sum(1 for line in data.splitlines() if line.strip()),
    }


def _require_id(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:\-]*", result):
        raise ValueError(f"invalid {field}: {result!r}")
    return result


def build_node(raw: Mapping[str, Any], canonical_ids: set[str]) -> EvidenceNode:
    node_id = _require_id(raw.get("node_id"), "node_id")
    node_type = str(raw.get("node_type", "")).strip()
    canonical_problem_id = str(raw.get("canonical_problem_id", "")).strip()
    title = str(raw.get("title", "")).strip()
    content = str(raw.get("content", "")).strip()
    scope = str(raw.get("scope", "")).strip()
    refs_raw = raw.get("source_refs")
    metadata = raw.get("metadata", {})
    if node_type not in NODE_TYPES:
        raise ValueError(f"{node_id}: unsupported node_type {node_type!r}")
    if canonical_problem_id not in canonical_ids:
        raise ValueError(f"{node_id}: unknown canonical_problem_id")
    if not title or not content or not scope:
        raise ValueError(f"{node_id}: title, content and scope are required")
    if not isinstance(refs_raw, list) or not all(isinstance(item, str) for item in refs_raw):
        raise ValueError(f"{node_id}: source_refs must be a string list")
    source_refs = tuple(sorted({item.strip() for item in refs_raw if item.strip()}))
    if not source_refs:
        raise ValueError(f"{node_id}: at least one source_ref is required")
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{node_id}: metadata must be an object")
    proof_claimed = bool(raw.get("proof_claimed", False))
    solution_claimed = bool(raw.get("solution_claimed", False))
    if solution_claimed:
        raise ValueError(f"{node_id}: solution claims are forbidden in ingestion")
    if proof_claimed and node_type != "formal_artifact":
        raise ValueError(f"{node_id}: only formal_artifact may carry proof_claimed")
    observed_at = parse_iso8601(str(raw.get("observed_at", "")), "observed_at")
    metadata_dict = dict(metadata)
    if node_type == "claim":
        requested = str(metadata_dict.get("requested_status", "candidate"))
        if requested not in PROMOTION_RANK:
            raise ValueError(f"{node_id}: invalid requested_status")
    if node_type == "evidence":
        kind = str(metadata_dict.get("evidence_kind", ""))
        if kind not in EVIDENCE_KINDS:
            raise ValueError(f"{node_id}: invalid evidence_kind")
    if node_type == "formal_artifact":
        if str(metadata_dict.get("proof_scope", "")) not in {"restricted", "general"}:
            raise ValueError(f"{node_id}: formal artifact requires restricted/general proof_scope")
        if not isinstance(metadata_dict.get("kernel_checked", False), bool):
            raise ValueError(f"{node_id}: kernel_checked must be boolean")
    if node_type == "independent_review":
        if str(metadata_dict.get("outcome", "")) not in {"accepted", "challenged", "rejected"}:
            raise ValueError(f"{node_id}: invalid review outcome")
    base = {
        "node_id": node_id,
        "node_type": node_type,
        "canonical_problem_id": canonical_problem_id,
        "title": title,
        "content": content,
        "scope": scope,
        "source_refs": source_refs,
        "observed_at": observed_at,
        "metadata": metadata_dict,
        "proof_claimed": proof_claimed,
        "solution_claimed": False,
    }
    return EvidenceNode(**base, node_digest=stable_digest(base))


def build_edge(raw: Mapping[str, Any], nodes: Mapping[str, EvidenceNode]) -> EvidenceEdge:
    edge_id = _require_id(raw.get("edge_id"), "edge_id")
    source_id = _require_id(raw.get("source_node_id"), "source_node_id")
    target_id = _require_id(raw.get("target_node_id"), "target_node_id")
    relation = str(raw.get("relation", "")).strip()
    scope = str(raw.get("scope", "")).strip()
    refs_raw = raw.get("evidence_refs")
    metadata = raw.get("metadata", {})
    if source_id not in nodes or target_id not in nodes:
        raise ValueError(f"{edge_id}: unknown source or target node")
    if source_id == target_id:
        raise ValueError(f"{edge_id}: self edges are forbidden")
    if relation not in RELATIONS:
        raise ValueError(f"{edge_id}: unsupported relation")
    if not scope:
        raise ValueError(f"{edge_id}: scope is required")
    if not isinstance(refs_raw, list) or not all(isinstance(item, str) for item in refs_raw):
        raise ValueError(f"{edge_id}: evidence_refs must be a string list")
    evidence_refs = tuple(sorted({item.strip() for item in refs_raw if item.strip()}))
    if relation != "merely_mentions" and not evidence_refs:
        raise ValueError(f"{edge_id}: evidential relation requires evidence_refs")
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{edge_id}: metadata must be an object")
    source = nodes[source_id]
    target = nodes[target_id]
    if source.canonical_problem_id != target.canonical_problem_id:
        cross_allowed = relation in {"generalizes", "specializes"} and metadata.get("cross_problem_relation") is True
        if not cross_allowed:
            raise ValueError(f"{edge_id}: cross-problem edge requires explicit generalization/specialization")
    _validate_relation_types(edge_id, relation, source.node_type, target.node_type)
    base = {
        "edge_id": edge_id,
        "source_node_id": source_id,
        "target_node_id": target_id,
        "relation": relation,
        "scope": scope,
        "evidence_refs": evidence_refs,
        "metadata": dict(metadata),
    }
    return EvidenceEdge(**base, edge_digest=stable_digest(base))


def _validate_relation_types(edge_id: str, relation: str, source_type: str, target_type: str) -> None:
    if relation in {"supports", "contradicts", "proves_restricted_case", "improves_bound"} and target_type != "claim":
        raise ValueError(f"{edge_id}: {relation} must target a claim")
    if relation == "depends_on" and not (source_type == "claim" and target_type == "assumption"):
        raise ValueError(f"{edge_id}: depends_on must be claim -> assumption")
    if relation == "discharges" and target_type not in {"assumption", "barrier"}:
        raise ValueError(f"{edge_id}: discharges must target assumption/barrier")
    if relation == "violates" and target_type not in {"assumption", "barrier"}:
        raise ValueError(f"{edge_id}: violates must target assumption/barrier")
    if relation == "scopes" and source_type not in {"barrier", "assumption"}:
        raise ValueError(f"{edge_id}: scopes must originate from barrier/assumption")
    if relation == "reproduces" and source_type not in {"computation_receipt", "formal_artifact", "independent_review"}:
        raise ValueError(f"{edge_id}: reproduces has invalid source type")
