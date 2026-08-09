from __future__ import annotations

from typing import Any

from .models import DocumentIR, NodeKind


EVIDENCE_KINDS = {
    NodeKind.CLAIM,
    NodeKind.THEOREM,
    NodeKind.RESULT,
    NodeKind.EXPERIMENT,
    NodeKind.CONJECTURE,
    NodeKind.PROPOSITION,
    NodeKind.LEMMA,
    NodeKind.COROLLARY,
}


def evidence_matrix(doc: DocumentIR) -> dict[str, Any]:
    sources = {source.id: source for source in doc.sources}
    rows: list[dict[str, Any]] = []
    for node in doc.nodes:
        if node.kind not in EVIDENCE_KINDS:
            continue
        declared_support = list(node.metadata.get("support", ())) if isinstance(node.metadata, dict) else []
        reviewed_sources = sorted(
            {
                str(item.get("source", ""))
                for item in declared_support
                if isinstance(item, dict)
                and item.get("reviewed") is True
                and str(item.get("relation", "")).lower() in {"supports", "derives", "measures", "verifies"}
                and str(item.get("source", "")) in sources
            }
        )
        rows.append(
            {
                "node_id": node.id,
                "kind": node.kind.value,
                "status": node.status,
                "sources": list(node.sources),
                "dependencies": list(node.dependencies),
                "reviewed_support_sources": reviewed_sources,
                "support_review_complete": bool(reviewed_sources) or not node.sources,
            }
        )
    return {
        "semantic_hash": doc.semantic_hash(),
        "rows": rows,
        "boundary": "registered sources and structural dependencies are evidence routing metadata, not automatic entailment",
    }
