from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Mapping

from omega_web_hg_t.models import stable_id, utc_now
from .extract import claims_from_sections, detect_duplicates
from .models import AbsorptionBundle
from .search import SearchIndex


def read_jsonl(path: Path) -> list[dict[str, object]]:
    result = []
    if not path.is_file():
        return result
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL {path}:{line_number}: {exc}") from exc
    return result


def compile_absorption(source_run: str | Path, output_dir: str | Path) -> AbsorptionBundle:
    source = Path(source_run)
    output = Path(output_dir)
    pages = read_jsonl(source / "pages.jsonl")
    sections = read_jsonl(source / "sections.jsonl")
    evidence = read_jsonl(source / "evidence.jsonl")
    if not pages or not evidence:
        raise ValueError("Source run must contain non-empty pages.jsonl and evidence.jsonl")
    page_by_id = {str(item["page_id"]): item for item in pages}
    claims = claims_from_sections(sections, page_by_id=page_by_id)
    duplicates = detect_duplicates(claims)

    nodes: dict[str, dict[str, object]] = {}
    edges: dict[str, dict[str, object]] = {}

    def add_node(node_id: str, kind: str, label: str, properties: Mapping[str, object]) -> None:
        nodes[node_id] = {"id": node_id, "kind": kind, "label": label, "properties": dict(properties)}

    def add_edge(relation: str, source_id: str, target_id: str, evidence_id: str = "") -> None:
        edge_id = stable_id("edge", relation, source_id, target_id, evidence_id)
        edges[edge_id] = {"edge_id": edge_id, "relation": relation, "source_id": source_id, "target_id": target_id, "evidence_id": evidence_id or None}

    for page in pages:
        add_node(str(page["page_id"]), "page", str(page.get("title") or page.get("canonical_url") or ""), page)
    for section in sections:
        add_node(str(section["section_id"]), "section", str(section.get("heading") or "Section"), section)
        add_edge("PAGE_CONTAINS_SECTION", str(section["page_id"]), str(section["section_id"]), str(page_by_id.get(str(section["page_id"]), {}).get("evidence_id") or ""))
    for item in evidence:
        add_node(str(item["evidence_id"]), "evidence", str(item.get("final_url") or ""), item)
    for claim in claims:
        add_node(claim.claim_id, "claim_candidate", claim.text[:120], asdict(claim))
        add_edge("SECTION_YIELDS_CLAIM_CANDIDATE", claim.section_id, claim.claim_id, claim.evidence_id)
        add_edge("CLAIM_CANDIDATE_EXTRACTED_FROM_EVIDENCE", claim.claim_id, claim.evidence_id, claim.evidence_id)
    for duplicate in duplicates:
        add_edge("CLAIM_DUPLICATE_OF", duplicate.member_id, duplicate.representative_id)

    graph = {
        "schema": "omega-web-hg-absorption-hypergraph/0.3",
        "source_run": str(source),
        "nodes": sorted(nodes.values(), key=lambda item: str(item["id"])),
        "hyperedges": sorted(edges.values(), key=lambda item: str(item["edge_id"])),
    }
    evidence_ids = {str(item["evidence_id"]) for item in evidence}
    section_ids = {str(item["section_id"]) for item in sections}
    orphan_claim_sections = [item.claim_id for item in claims if item.section_id not in section_ids]
    orphan_claim_evidence = [item.claim_id for item in claims if item.evidence_id not in evidence_ids]
    node_ids = set(nodes)
    orphan_edges = [edge_id for edge_id, edge in edges.items() if str(edge["source_id"]) not in node_ids or str(edge["target_id"]) not in node_ids]
    report = {
        "schema": "omega-web-hg-absorption-report/0.3",
        "created_at": utc_now(),
        "status": "PASS_R0_3" if not orphan_claim_sections and not orphan_claim_evidence and not orphan_edges else "FAIL_R0_3",
        "source_run": str(source),
        "pages": len(pages),
        "sections": len(sections),
        "claim_candidates": len(claims),
        "duplicates": len(duplicates),
        "exact_duplicates": sum(item.kind == "exact" for item in duplicates),
        "near_duplicates": sum(item.kind == "near" for item in duplicates),
        "orphan_claim_sections": orphan_claim_sections,
        "orphan_claim_evidence": orphan_claim_evidence,
        "orphan_edges": orphan_edges,
        "boundary": "Sentence extraction and similarity are organizational heuristics; they do not verify truth, entailment, novelty, ownership, or permission to publish.",
    }
    bundle = AbsorptionBundle(str(source), claims, duplicates, graph, report)
    bundle.write(output)
    with SearchIndex(output / "search.sqlite3") as index:
        index.build(pages=pages, sections=sections, claims=claims)
        report["search_documents"] = index.count()
        report["fts5_enabled"] = index.fts_enabled
    (output / "absorption-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    bundle.report = report
    return bundle


def audit_absorption(output_dir: str | Path) -> dict[str, object]:
    root = Path(output_dir)
    required = {"manifest.json", "claim-candidates.jsonl", "duplicates.jsonl", "absorption-hypergraph.json", "absorption-report.json", "search.sqlite3"}
    missing = sorted(name for name in required if not (root / name).is_file())
    findings: list[str] = []
    if missing:
        findings.append(f"missing outputs: {missing}")
    claims = read_jsonl(root / "claim-candidates.jsonl")
    graph = json.loads((root / "absorption-hypergraph.json").read_text(encoding="utf-8")) if (root / "absorption-hypergraph.json").is_file() else {"nodes": [], "hyperedges": []}
    node_ids = {str(item["id"]) for item in graph.get("nodes", [])}
    orphan_edges = [str(item.get("edge_id")) for item in graph.get("hyperedges", []) if str(item.get("source_id")) not in node_ids or str(item.get("target_id")) not in node_ids]
    if orphan_edges:
        findings.append(f"orphan edges: {orphan_edges[:20]}")
    with SearchIndex(root / "search.sqlite3") as index:
        indexed = index.count()
    minimum = len(claims)
    if indexed < minimum:
        findings.append(f"search index incomplete: {indexed} < {minimum}")
    return {
        "schema": "omega-web-hg-absorption-audit/0.3",
        "status": "PASS_R0_3" if not findings else "FAIL_R0_3",
        "claims": len(claims),
        "indexed_documents": indexed,
        "findings": findings,
    }
