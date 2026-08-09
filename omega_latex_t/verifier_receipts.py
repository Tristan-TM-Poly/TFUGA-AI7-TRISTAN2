from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from .models import DocumentIR, Node


class VerifierReceiptError(ValueError):
    pass


SYSTEMS = {"lean", "coq", "isabelle"}
STATUSES = {"passed", "failed", "unknown"}


def statement_sha256(statement: str) -> str:
    return sha256(statement.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerifierReceipt:
    system: str
    theorem_id: str
    statement_sha256: str
    status: str
    verifier_version: str
    artifact_sha256: str
    run_id: str = ""
    timestamp: str = ""
    provenance: Mapping[str, Any] = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "VerifierReceipt":
        item = cls(system=str(data.get("system", "")).lower(), theorem_id=str(data.get("theorem_id", "")), statement_sha256=str(data.get("statement_sha256", "")).lower(), status=str(data.get("status", "unknown")).lower(), verifier_version=str(data.get("verifier_version", "")), artifact_sha256=str(data.get("artifact_sha256", "")).lower(), run_id=str(data.get("run_id", "")), timestamp=str(data.get("timestamp", "")), provenance=dict(data.get("provenance", {})))
        item.validate(); return item

    def validate(self) -> None:
        if self.system not in SYSTEMS: raise VerifierReceiptError(f"unsupported verifier system {self.system!r}")
        if not self.theorem_id: raise VerifierReceiptError("theorem_id is required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.statement_sha256): raise VerifierReceiptError("statement_sha256 must be 64 lowercase hex characters")
        if self.status not in STATUSES: raise VerifierReceiptError(f"unsupported verifier status {self.status!r}")
        if not self.verifier_version: raise VerifierReceiptError("verifier_version is required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.artifact_sha256): raise VerifierReceiptError("artifact_sha256 must be 64 lowercase hex characters")

    def to_mapping(self) -> dict[str, Any]:
        return {"system": self.system, "theorem_id": self.theorem_id, "statement_sha256": self.statement_sha256, "status": self.status, "verifier_version": self.verifier_version, "artifact_sha256": self.artifact_sha256, "run_id": self.run_id, "timestamp": self.timestamp, "provenance": dict(self.provenance or {}), "receipt_sha256": self.digest()}

    def digest(self) -> str:
        raw = json.dumps({"system": self.system, "theorem_id": self.theorem_id, "statement_sha256": self.statement_sha256, "status": self.status, "verifier_version": self.verifier_version, "artifact_sha256": self.artifact_sha256, "run_id": self.run_id, "timestamp": self.timestamp, "provenance": dict(self.provenance or {})}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(raw).hexdigest()


def validate_receipt_for_theorem(receipt: VerifierReceipt, theorem: Node) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []; formal_system = str(theorem.metadata.get("formal_system", "")).lower(); formal_statement = str(theorem.metadata.get("formal_statement", ""))
    if receipt.theorem_id != theorem.id: reasons.append("theorem_id_mismatch")
    if not formal_system: reasons.append("formal_system_missing")
    elif receipt.system != formal_system: reasons.append("formal_system_mismatch")
    if not formal_statement: reasons.append("formal_statement_missing")
    elif receipt.statement_sha256 != statement_sha256(formal_statement): reasons.append("statement_hash_mismatch")
    if receipt.status != "passed": reasons.append("verifier_status_not_passed")
    expected_artifact = str(theorem.metadata.get("formal_artifact_sha256", "")).lower()
    if expected_artifact and expected_artifact != receipt.artifact_sha256: reasons.append("artifact_hash_mismatch")
    return not reasons, tuple(reasons)


def verifier_receipt_report(doc: DocumentIR) -> dict[str, Any]:
    raw_receipts = doc.provenance.get("verifier_receipts", ()) if isinstance(doc.provenance, Mapping) else (); theorem_by_id = {node.id: node for node in doc.nodes}; entries = []
    for index, raw in enumerate(raw_receipts if isinstance(raw_receipts, (list, tuple)) else ()):
        try: receipt = VerifierReceipt.from_mapping(raw)
        except (VerifierReceiptError, TypeError) as exc:
            entries.append({"index": index, "valid_receipt": False, "verified_match": False, "reasons": [f"receipt_invalid:{exc}"]}); continue
        theorem = theorem_by_id.get(receipt.theorem_id)
        if theorem is None:
            entries.append({"index": index, "valid_receipt": True, "verified_match": False, "receipt": receipt.to_mapping(), "reasons": ["theorem_missing"]}); continue
        verified, reasons = validate_receipt_for_theorem(receipt, theorem)
        entries.append({"index": index, "valid_receipt": True, "verified_match": verified, "receipt": receipt.to_mapping(), "reasons": list(reasons)})
    return {"semantic_hash": doc.semantic_hash(), "entries": entries, "verified_count": sum(1 for item in entries if item.get("verified_match") is True), "boundary": "receipts attest that an external verifier reported success for an exact statement/artifact hash; they do not establish natural-language equivalence or scientific truth"}


def matching_receipt(doc: DocumentIR, theorem: Node) -> VerifierReceipt | None:
    raw_receipts = doc.provenance.get("verifier_receipts", ()) if isinstance(doc.provenance, Mapping) else (); matches: list[VerifierReceipt] = []
    if not isinstance(raw_receipts, (list, tuple)): return None
    for raw in raw_receipts:
        try: receipt = VerifierReceipt.from_mapping(raw)
        except (VerifierReceiptError, TypeError): continue
        verified, _ = validate_receipt_for_theorem(receipt, theorem)
        if verified: matches.append(receipt)
    if not matches: return None
    return sorted(matches, key=lambda item: (item.timestamp, item.run_id, item.digest()))[-1]
