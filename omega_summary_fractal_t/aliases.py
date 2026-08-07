from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .summarizer import deterministic_timestamp


def _canonical_entry(entry: Mapping[str, Any], previous_hash: str) -> bytes:
    payload = {
        "previous_hash": previous_hash,
        "source": str(entry.get("source", "")),
        "target": str(entry.get("target", "")),
        "evidence_ref": str(entry.get("evidence_ref", "")),
        "approved_by": str(entry.get("approved_by", "")),
        "approved_at": str(entry.get("approved_at", "")),
        "note": str(entry.get("note", "")),
        "status": str(entry.get("status", "approved")),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _entry_hash(entry: Mapping[str, Any], previous_hash: str) -> str:
    return hashlib.sha256(_canonical_entry(entry, previous_hash)).hexdigest()


def load_alias_registry(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {
            "schema_version": "1.0.0",
            "entries": [],
            "boundary": "only explicitly approved aliases are authoritative inside this registry; identity candidates never rewrite history automatically",
        }
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError("invalid alias registry")
    return payload


def verify_alias_registry(registry: Mapping[str, Any]) -> bool:
    previous_hash = ""
    for ordinal, item in enumerate(registry.get("entries", []), start=1):
        if int(item.get("ordinal", 0)) != ordinal:
            return False
        if str(item.get("previous_hash", "")) != previous_hash:
            return False
        expected = _entry_hash(item, previous_hash)
        if str(item.get("entry_hash", "")) != expected:
            return False
        previous_hash = expected
    return True


def _mapping(registry: Mapping[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in registry.get("entries", []):
        if item.get("status") == "approved":
            mapping[str(item.get("source", ""))] = str(item.get("target", ""))
    return mapping


def resolve_alias(identifier: str, registry: Mapping[str, Any]) -> str:
    mapping = _mapping(registry)
    current = identifier
    seen: set[str] = set()
    while current in mapping:
        if current in seen:
            raise ValueError("alias cycle detected")
        seen.add(current)
        current = mapping[current]
    return current


def approve_alias(
    registry_path: str | Path,
    *,
    source: str,
    target: str,
    evidence_ref: str,
    approved_by: str,
    note: str = "",
) -> dict[str, Any]:
    """Append one human-approved alias to a hash-chained registry.

    This action is intentionally distinct from identity-candidate generation. An
    identity continuity score can suggest a relation, but only this explicit
    approval path makes it authoritative inside the alias registry.
    """

    if not source or not target or source == target:
        raise ValueError("source and target must be distinct non-empty identifiers")
    if not evidence_ref or not approved_by:
        raise ValueError("evidence_ref and approved_by are required")

    registry = load_alias_registry(registry_path)
    if not verify_alias_registry(registry):
        raise ValueError("alias registry hash chain is invalid")
    mapping = _mapping(registry)
    if source in mapping:
        if mapping[source] == target:
            return registry
        raise ValueError(f"source already has an approved alias target: {source}")

    probe = target
    seen = {source}
    while probe in mapping:
        if probe in seen:
            raise ValueError("alias approval would create a cycle")
        seen.add(probe)
        probe = mapping[probe]
    if probe == source:
        raise ValueError("alias approval would create a cycle")

    previous_hash = str(registry["entries"][-1]["entry_hash"]) if registry["entries"] else ""
    entry: dict[str, Any] = {
        "ordinal": len(registry["entries"]) + 1,
        "previous_hash": previous_hash,
        "source": source,
        "target": target,
        "evidence_ref": evidence_ref,
        "approved_by": approved_by,
        "approved_at": deterministic_timestamp(),
        "note": note,
        "status": "approved",
    }
    entry["entry_hash"] = _entry_hash(entry, previous_hash)
    registry["entries"].append(entry)
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


def identity_proposals(identity_report: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(identity_report, Mapping):
        payload = dict(identity_report)
    else:
        payload = json.loads(Path(identity_report).read_text(encoding="utf-8"))
    proposals = []
    for item in payload.get("candidates", []):
        if item.get("status") != "review_required":
            continue
        source = item.get("from")
        target = item.get("to")
        if not source or not target:
            continue
        proposals.append(
            {
                "source": source,
                "target": target,
                "score": item.get("score"),
                "evidence": item.get("evidence"),
                "one_to_one": bool(item.get("one_to_one")),
                "status": "proposal_only",
                "automatic_approval": False,
            }
        )
    return {
        "schema_version": "1.0.0",
        "proposals": proposals,
        "boundary": "identity proposals are non-authoritative until an explicit alias approval is recorded with evidence and approver identity",
    }
