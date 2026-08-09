from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .models import DocumentIR, NodeKind


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _content_fingerprint(kind: str, title: str, content: str) -> str:
    raw = json.dumps({"kind": kind, "title": _normalize_text(title), "content": _normalize_text(content)}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def metadocument_graph(documents: Mapping[str, DocumentIR] | Iterable[tuple[str, DocumentIR]]) -> dict[str, Any]:
    items = dict(documents); docs = []; global_nodes = []; fingerprint_groups: dict[str, list[str]] = {}; canonical_groups: dict[str, list[dict[str, Any]]] = {}; source_users: dict[str, set[str]] = {}; internal_edges: list[dict[str, str]] = []
    for doc_id in sorted(items):
        doc = items[doc_id]
        docs.append({"document_id": doc_id, "title": doc.meta.title, "semantic_hash": doc.semantic_hash(), "node_count": len(doc.nodes), "source_count": len(doc.sources)})
        by_id = {node.id: node for node in doc.nodes}; dependents = {node.id: set() for node in doc.nodes}
        for node in doc.nodes:
            for dep in node.dependencies:
                if dep in dependents: dependents[dep].add(node.id)
                if dep in by_id: internal_edges.append({"relation": "depends_on", "source": f"{doc_id}:{node.id}", "target": f"{doc_id}:{dep}"})
        for node in doc.nodes:
            global_id = f"{doc_id}:{node.id}"; fingerprint = _content_fingerprint(node.kind.value, node.title, node.content)
            fingerprint_groups.setdefault(fingerprint, []).append(global_id)
            canonical_key = str(node.metadata.get("canonical_key", "")).strip() if isinstance(node.metadata, Mapping) else ""
            if canonical_key: canonical_groups.setdefault(canonical_key, []).append({"global_id": global_id, "kind": node.kind.value, "status": node.status, "normalized_content": _normalize_text(node.content), "content": node.content})
            for source_id in node.sources: source_users.setdefault(source_id, set()).add(global_id)
            orphan = node.kind not in {NodeKind.SECTION, NodeKind.WARNING, NodeKind.APPENDIX} and not node.dependencies and not dependents.get(node.id)
            global_nodes.append({"global_id": global_id, "document_id": doc_id, "node_id": node.id, "kind": node.kind.value, "title": node.title, "status": node.status, "content_fingerprint": fingerprint, "canonical_key": canonical_key, "orphan_candidate": orphan})
    duplicate_groups = [{"content_fingerprint": fingerprint, "nodes": sorted(nodes)} for fingerprint, nodes in sorted(fingerprint_groups.items()) if len({node.split(":", 1)[0] for node in nodes}) > 1]
    conflict_candidates = []
    for key, group in sorted(canonical_groups.items()):
        if len({item["normalized_content"] for item in group}) > 1:
            conflict_candidates.append({"canonical_key": key, "nodes": [{"global_id": item["global_id"], "kind": item["kind"], "status": item["status"], "content": item["content"]} for item in group], "reason": "same canonical_key with different normalized content"})
    cross_edges: list[dict[str, Any]] = []
    for group in duplicate_groups:
        nodes = group["nodes"]
        for index, source in enumerate(nodes):
            for target in nodes[index + 1:]: cross_edges.append({"relation": "duplicate_candidate", "source": source, "target": target})
    for source_id, users in sorted(source_users.items()):
        ordered = sorted(users)
        if len({user.split(":",1)[0] for user in ordered}) < 2: continue
        for index, source in enumerate(ordered):
            for target in ordered[index+1:]:
                if source.split(":",1)[0] != target.split(":",1)[0]: cross_edges.append({"relation":"shared_source","source":source,"target":target,"source_id":source_id})
    return {"schema_version":"1.0.0","documents":docs,"nodes":global_nodes,"edges":internal_edges+cross_edges,"duplicate_candidates":duplicate_groups,"conflict_candidates":conflict_candidates,"orphan_candidates":sorted(node["global_id"] for node in global_nodes if node["orphan_candidate"]),"source_usage":{key:sorted(value) for key,value in sorted(source_users.items())},"boundary":"duplicate/conflict/orphan labels are structural review candidates only; they are not proofs of semantic equivalence, contradiction, obsolescence or invalidity"}
