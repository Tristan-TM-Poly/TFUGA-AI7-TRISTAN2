from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from .compiler import DocumentCompiler
from .models import DocumentIR, NodeKind
from .verifier_receipts import matching_receipt


def _safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not name:
        name = "omega_theorem"
    if name[0].isdigit():
        name = "omega_" + name
    return name


def theorem_bundle(doc: DocumentIR, theorem_id: str) -> dict[str, Any]:
    by_id = {node.id: node for node in doc.nodes}
    if theorem_id not in by_id:
        raise KeyError(theorem_id)
    theorem = by_id[theorem_id]
    if theorem.kind not in {NodeKind.THEOREM, NodeKind.LEMMA, NodeKind.PROPOSITION, NodeKind.COROLLARY, NodeKind.CONJECTURE}:
        raise ValueError(f"{theorem_id!r} is not a theorem-like node")
    proof_nodes = [node for node in doc.nodes if node.kind in {NodeKind.PROOF, NodeKind.PROOF_SKETCH} and (theorem.id in node.dependencies or node.id in theorem.dependencies)]
    formal_system = str(theorem.metadata.get("formal_system", ""))
    formal_statement = str(theorem.metadata.get("formal_statement", ""))
    metadata_verified = theorem.metadata.get("formal_verified") is True
    numerical_contract = theorem.metadata.get("numerical_test_contract", {})
    receipt = matching_receipt(doc, theorem)
    formal_status = "verified-external-receipt" if receipt is not None else ("stub-or-unverified" if formal_statement else "no-formal-statement")
    return {
        "schema_version": "1.1.0",
        "theorem": {"id": theorem.id, "kind": theorem.kind.value, "title": theorem.title, "statement": theorem.content, "status": theorem.status, "dependencies": list(theorem.dependencies), "sources": list(theorem.sources), "source_locators": dict(theorem.source_locators)},
        "proof_nodes": [{"id": node.id, "kind": node.kind.value, "status": node.status, "dependencies": list(node.dependencies)} for node in proof_nodes],
        "formal_projection": {"system": formal_system, "statement_supplied": bool(formal_statement), "metadata_verified_flag_supplied": metadata_verified, "external_receipt": receipt.to_mapping() if receipt else None, "status": formal_status},
        "numerical_test_contract": numerical_contract if isinstance(numerical_contract, dict) else {},
        "boundary": "narrative proof, formal verifier receipt and numerical evidence remain distinct; bare metadata flags never certify; generated stubs are never proof",
    }


def write_theorem_bundle(doc: DocumentIR, theorem_id: str, output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = theorem_bundle(doc, theorem_id)
    theorem = next(node for node in doc.nodes if node.id == theorem_id)
    compiler = DocumentCompiler(fail_on_audit_error=False)
    theorem_json = out / "theorem.json"
    theorem_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    theorem_tex = out / "theorem.tex"
    theorem_tex.write_text(compiler.render_node(theorem, doc) + "\n", encoding="utf-8")
    proof_graph = out / "proof_graph.json"
    proof_graph.write_text(json.dumps({"theorem_id": theorem_id, "dependencies": list(theorem.dependencies), "proof_nodes": payload["proof_nodes"], "sources": list(theorem.sources), "source_locators": dict(theorem.source_locators)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    formal_path = out / "formal_stub.lean"
    formal = payload["formal_projection"]
    formal_statement = str(theorem.metadata.get("formal_statement", ""))
    system = str(theorem.metadata.get("formal_system", ""))
    if system.lower() == "lean" and formal_statement:
        formal_path.write_text("-- AUTO-GENERATED PROOF OBLIGATION STUB; placeholder remains unverified here.\n" + f"theorem {_safe_name(theorem.id)} : {formal_statement} := by\n" + "  sorry\n", encoding="utf-8")
    else:
        formal_path.write_text("-- No Lean formal statement supplied.\n-- This file is a projection placeholder, not a proof artifact.\n", encoding="utf-8")
    numerical_path = out / "numerical-test-contract.json"
    numerical_path.write_text(json.dumps(payload["numerical_test_contract"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_path = out / "formal-verifier-receipt.json"
    receipt_path.write_text(json.dumps(formal.get("external_receipt"), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths = {"theorem": theorem_json, "latex": theorem_tex, "proof_graph": proof_graph, "formal_stub": formal_path, "numerical_contract": numerical_path, "formal_receipt": receipt_path}
    manifest = {"schema_version": "1.1.0", "theorem_id": theorem_id, "semantic_hash": doc.semantic_hash(), "artifacts": {name: {"path": path.name, "sha256": sha256(path.read_bytes()).hexdigest()} for name, path in paths.items()}, "formal_status": formal["status"], "boundary": payload["boundary"]}
    manifest_path = out / "bundle-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["manifest"] = manifest_path
    return paths
