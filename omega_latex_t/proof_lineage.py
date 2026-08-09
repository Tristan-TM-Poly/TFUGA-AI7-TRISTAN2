from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


class ProofLineageError(ValueError):
    pass


def proof_lineage(doc: Any) -> dict[str, Any]:
    provenance=dict(getattr(doc,"provenance",{}) or {})
    raw_receipts=provenance.get("verifier_receipts",())
    receipts=[dict(x) for x in raw_receipts if isinstance(x,Mapping)]
    nodes_by_id: dict[str, dict[str, Any]]={}; edges=[]; receipt_ids=set()
    theorem_ids={str(getattr(node,"id","")) for node in getattr(doc,"nodes",()) if str(getattr(getattr(node,"kind",None),"value",getattr(node,"kind",""))) == "theorem"}
    for theorem_id in sorted(x for x in theorem_ids if x):
        nodes_by_id[f"theorem:{theorem_id}"]={"id":f"theorem:{theorem_id}","kind":"theorem"}
    for index,receipt in enumerate(receipts):
        rid=str(receipt.get("receipt_id") or f"receipt-{index+1}")
        if rid in receipt_ids: raise ProofLineageError(f"duplicate receipt id {rid!r}")
        receipt_ids.add(rid)
        theorem_id=str(receipt.get("theorem_id","")); system=str(receipt.get("system",receipt.get("verifier",""))); status=str(receipt.get("status","unknown"))
        digest=sha256(json.dumps(receipt,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
        nodes_by_id[rid]={"id":rid,"kind":"verifier_receipt","system":system,"status":status,"receipt_sha256":digest}
        if theorem_id:
            theorem_node=f"theorem:{theorem_id}"; nodes_by_id.setdefault(theorem_node,{"id":theorem_node,"kind":"theorem","external":theorem_id not in theorem_ids}); edges.append({"source":theorem_node,"target":rid,"kind":"verified_by"})
        artifact=str(receipt.get("artifact_sha256",""))
        if artifact:
            artifact_node=f"artifact:{artifact}"; nodes_by_id.setdefault(artifact_node,{"id":artifact_node,"kind":"proof_artifact","sha256":artifact}); edges.append({"source":rid,"target":artifact_node,"kind":"attests_artifact"})
        parent=str(receipt.get("parent_receipt_id",""))
        if parent: edges.append({"source":parent,"target":rid,"kind":"derives_receipt"})
    referenced={e["source"] for e in edges if e["kind"]=="derives_receipt"}
    missing=sorted(x for x in referenced if x not in receipt_ids)
    findings=[{"code":"PROOF_LINEAGE_PARENT_MISSING","severity":"error","message":f"missing parent receipt {x}"} for x in missing]
    return {"schema_version":"1.0.0","semantic_hash":getattr(doc,"semantic_hash",lambda:"")(),"nodes":[nodes_by_id[k] for k in sorted(nodes_by_id)],"edges":edges,"findings":findings,"boundary":"lineage records verifier/artifact relationships; it does not establish natural-language equivalence, theorem importance, trustworthiness of the verifier environment or absence of specification errors"}
