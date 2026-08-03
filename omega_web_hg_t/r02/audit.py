from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


def _jsonl(path: Path) -> list[dict[str, object]]:
    records = []
    if not path.is_file():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL {path}:{line_number}: {exc}") from exc
    return records


def audit_run(root: str | Path) -> dict[str, object]:
    directory = Path(root)
    required = {
        "manifest.json",
        "pages.jsonl",
        "sections.jsonl",
        "edges.jsonl",
        "evidence.jsonl",
        "versions.jsonl",
        "changes.jsonl",
        "discoveries.jsonl",
        "oak-report.json",
        "hypergraph.json",
        "hypergraph-v2.json",
        "hypergraph-v2.graphml",
        "provenance.jsonld",
    }
    missing = sorted(name for name in required if not (directory / name).is_file())
    findings: list[str] = []
    if missing:
        findings.append(f"missing outputs: {missing}")
    pages = _jsonl(directory / "pages.jsonl")
    sections = _jsonl(directory / "sections.jsonl")
    edges = _jsonl(directory / "edges.jsonl")
    evidence = _jsonl(directory / "evidence.jsonl")
    versions = _jsonl(directory / "versions.jsonl")
    node_ids = {str(item["page_id"]) for item in pages} | {str(item["section_id"]) for item in sections}
    if (directory / "url-candidates.jsonl").is_file():
        node_ids |= {str(item["node_id"]) for item in _jsonl(directory / "url-candidates.jsonl")}
    orphan_edges = [str(item.get("edge_id")) for item in edges if str(item.get("source_id")) not in node_ids or str(item.get("target_id")) not in node_ids]
    if orphan_edges:
        findings.append(f"orphan edges: {orphan_edges[:20]}")
    evidence_ids = {str(item["evidence_id"]) for item in evidence}
    orphan_page_evidence = [str(item["page_id"]) for item in pages if str(item.get("evidence_id")) not in evidence_ids]
    if orphan_page_evidence:
        findings.append(f"orphan page evidence: {orphan_page_evidence[:20]}")
    hash_mismatches = []
    for item in evidence:
        relative = item.get("raw_blob")
        if not relative:
            continue
        path = directory / str(relative)
        if not path.is_file():
            hash_mismatches.append(f"missing:{relative}")
            continue
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != item.get("content_sha256"):
            hash_mismatches.append(f"hash:{relative}")
    if hash_mismatches:
        findings.append(f"raw object mismatches: {hash_mismatches[:20]}")
    if (directory / "hypergraph-v2.json").is_file():
        graph_v2 = json.loads((directory / "hypergraph-v2.json").read_text(encoding="utf-8"))
        graph_node_ids = {str(item["id"]) for item in graph_v2.get("nodes", [])}
        graph_orphans = [str(item.get("edge_id")) for item in graph_v2.get("hyperedges", []) if str(item.get("source_id")) not in graph_node_ids or str(item.get("target_id")) not in graph_node_ids]
        if graph_orphans:
            findings.append(f"v2 orphan edges: {graph_orphans[:20]}")
    if (directory / "provenance.jsonld").is_file():
        provenance = json.loads((directory / "provenance.jsonld").read_text(encoding="utf-8"))
        if "@context" not in provenance or "@graph" not in provenance:
            findings.append("invalid JSON-LD provenance envelope")
    duplicate_versions = len(versions) - len({str(item["version_id"]) for item in versions})
    if duplicate_versions:
        findings.append(f"duplicate versions: {duplicate_versions}")
    return {
        "schema": "omega-web-hg-audit/0.2",
        "status": "PASS_R0_2" if not findings else "FAIL_R0_2",
        "root": str(directory),
        "counts": {
            "pages": len(pages),
            "sections": len(sections),
            "edges": len(edges),
            "evidence": len(evidence),
            "versions": len(versions),
        },
        "missing": missing,
        "findings": findings,
    }
