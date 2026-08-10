from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


class ProofLineageError(ValueError):
    pass


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    return sha256(json.dumps(dict(receipt), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def proof_lineage(doc: Any) -> dict[str, Any]:
    provenance = dict(getattr(doc, "provenance", {}) or {})
    raw_receipts = provenance.get("verifier_receipts", ())
    findings: list[dict[str, str]] = []
    receipts: list[dict[str, Any]] = []
    if not isinstance(raw_receipts, (list, tuple)):
        findings.append({"code": "PROOF_LINEAGE_RECEIPTS_INVALID", "severity": "error", "message": "verifier_receipts must be an array"})
        raw_receipts = ()

    for index, raw in enumerate(raw_receipts):
        if not isinstance(raw, Mapping):
            findings.append({"code": "PROOF_LINEAGE_RECEIPT_INVALID", "severity": "error", "message": f"receipt {index} must be an object"})
            continue
        receipts.append(dict(raw))

    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    receipt_ids: set[str] = set()
    parent_by_receipt: dict[str, str] = {}
    theorem_ids = {
        str(getattr(node, "id", ""))
        for node in getattr(doc, "nodes", ())
        if str(getattr(getattr(node, "kind", None), "value", getattr(node, "kind", ""))) == "theorem"
    }
    for theorem_id in sorted(x for x in theorem_ids if x):
        nodes_by_id[f"theorem:{theorem_id}"] = {"id": f"theorem:{theorem_id}", "kind": "theorem"}

    for index, receipt in enumerate(receipts):
        rid = str(receipt.get("receipt_id") or f"receipt-{index+1}")
        if rid in receipt_ids:
            findings.append({"code": "PROOF_LINEAGE_DUPLICATE_RECEIPT_ID", "severity": "error", "message": f"duplicate receipt id {rid!r}"})
            continue
        receipt_ids.add(rid)

        theorem_id = str(receipt.get("theorem_id", ""))
        system = str(receipt.get("system", receipt.get("verifier", "")))
        status = str(receipt.get("status", "unknown"))
        nodes_by_id[rid] = {"id": rid, "kind": "verifier_receipt", "system": system, "status": status, "receipt_sha256": _receipt_digest(receipt)}

        if theorem_id:
            theorem_node = f"theorem:{theorem_id}"
            nodes_by_id.setdefault(theorem_node, {"id": theorem_node, "kind": "theorem", "external": theorem_id not in theorem_ids})
            edges.append({"source": theorem_node, "target": rid, "kind": "verified_by"})

        artifact = str(receipt.get("artifact_sha256", ""))
        if artifact:
            artifact_node = f"artifact:{artifact}"
            nodes_by_id.setdefault(artifact_node, {"id": artifact_node, "kind": "proof_artifact", "sha256": artifact})
            edges.append({"source": rid, "target": artifact_node, "kind": "attests_artifact"})

        parent = str(receipt.get("parent_receipt_id", ""))
        if parent:
            if parent == rid:
                findings.append({"code": "PROOF_LINEAGE_SELF_PARENT", "severity": "error", "message": f"receipt {rid!r} cannot derive from itself"})
            else:
                parent_by_receipt[rid] = parent
                edges.append({"source": parent, "target": rid, "kind": "derives_receipt"})

    for rid, parent in sorted(parent_by_receipt.items()):
        if parent not in receipt_ids:
            findings.append({"code": "PROOF_LINEAGE_PARENT_MISSING", "severity": "error", "message": f"missing parent receipt {parent}"})

    state: dict[str, int] = {}
    for start in sorted(receipt_ids):
        if state.get(start) == 2:
            continue
        path: list[str] = []
        positions: dict[str, int] = {}
        current = start
        while current in receipt_ids and state.get(current, 0) != 2:
            if current in positions:
                cycle = path[positions[current]:] + [current]
                findings.append({"code": "PROOF_LINEAGE_CYCLE", "severity": "error", "message": "receipt parent cycle: " + " -> ".join(cycle)})
                break
            positions[current] = len(path)
            path.append(current)
            state[current] = 1
            current = parent_by_receipt.get(current, "")
            if not current:
                break
        for node_id in path:
            state[node_id] = 2

    return {
        "schema_version": "1.0.1",
        "semantic_hash": getattr(doc, "semantic_hash", lambda: "")(),
        "nodes": [nodes_by_id[k] for k in sorted(nodes_by_id)],
        "edges": edges,
        "findings": findings,
        "boundary": "lineage records verifier/artifact relationships; it does not establish natural-language equivalence, theorem importance, trustworthiness of the verifier environment or absence of specification errors",
    }
