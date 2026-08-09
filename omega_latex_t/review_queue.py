from __future__ import annotations

from typing import Any, Mapping


def metadocument_review_queue(graph: Mapping[str, Any]) -> dict[str, Any]:
    items=[]
    for conflict in graph.get("conflict_candidates",()):
        if not isinstance(conflict,Mapping): continue
        items.append({"priority":100,"kind":"canonical-key-conflict","subject":str(conflict.get("canonical_key",conflict.get("key",""))),"payload":dict(conflict),"required_action":"human semantic review"})
    for duplicate in graph.get("duplicate_candidates",()):
        if not isinstance(duplicate,Mapping): continue
        items.append({"priority":60,"kind":"exact-duplicate-candidate","subject":str(duplicate.get("content_fingerprint",duplicate.get("hash",duplicate.get("semantic_hash","")))),"payload":dict(duplicate),"required_action":"deduplication review"})
    for orphan in graph.get("orphan_candidates",()):
        if isinstance(orphan,Mapping):
            subject=str(orphan.get("global_id",orphan.get("id",orphan.get("node_id","")))); payload=dict(orphan)
        else:
            subject=str(orphan); payload={"global_id":subject}
        items.append({"priority":20,"kind":"orphan-candidate","subject":subject,"payload":payload,"required_action":"linkage/context review"})
    items.sort(key=lambda x:(-x["priority"],x["kind"],x["subject"]))
    return {"schema_version":"1.0.0","count":len(items),"items":items,"boundary":"queue prioritizes structural review candidates only; it does not declare contradictions, plagiarism, equivalence, novelty or error"}
