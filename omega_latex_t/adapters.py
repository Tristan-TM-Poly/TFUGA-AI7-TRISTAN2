from __future__ import annotations

from dataclasses import replace
import re
from typing import Any, Mapping

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    return value or "node"


def markdown_to_document(text: str, *, title: str = "Imported Markdown", author: str = "", language: str = "en") -> DocumentIR:
    """Conservative Markdown adapter; it does not infer theorem/proof status."""
    nodes: list[Node] = []
    paragraph: list[str] = []
    equation: list[str] = []
    in_math = False
    ordinal = 0

    def flush_paragraph() -> None:
        nonlocal ordinal
        if paragraph:
            ordinal += 1
            nodes.append(Node(id=f"md.p.{ordinal}", kind=NodeKind.PARAGRAPH, content=" ".join(x.strip() for x in paragraph).strip(), status="imported", metadata={"adapter": "markdown", "semantic_inference": False}))
            paragraph.clear()

    def flush_equation() -> None:
        nonlocal ordinal
        ordinal += 1
        nodes.append(Node(id=f"md.eq.{ordinal}", kind=NodeKind.EQUATION, content="\n".join(equation).strip(), status="imported", metadata={"adapter": "markdown", "semantic_inference": False}))
        equation.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip() == "$$":
            if in_math:
                flush_equation(); in_math = False
            else:
                flush_paragraph(); in_math = True
            continue
        if in_math:
            equation.append(line); continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush_paragraph(); ordinal += 1
            nodes.append(Node(id=f"md.sec.{ordinal}", kind=NodeKind.SECTION, title=match.group(2).strip(), content="", status="imported", metadata={"markdown_level": len(match.group(1)), "adapter": "markdown"}))
            continue
        if not line.strip(): flush_paragraph()
        else: paragraph.append(line)
    if in_math:
        raise ValueError("unterminated $$ display-math block")
    flush_paragraph()
    return DocumentIR(meta=DocumentMeta(title=title, author=author, language=language), nodes=tuple(nodes), provenance={"adapter": "markdown", "semantic_inference": False})


def summary_bundle_to_document(payload: Mapping[str, Any]) -> DocumentIR:
    """Project omega_summary_fractal_t-style nodes/edges without promoting arbitrary graph edges to proof dependencies."""
    root = str(payload.get("root", "Repository Summary"))
    nodes: list[Node] = [Node(id="summary.root", kind=NodeKind.SECTION, title=f"Repository summary: {root}", content="", status="imported")]
    seen: set[str] = {"summary.root"}
    for ordinal, item in enumerate(payload.get("nodes", ()), start=1):
        raw_id = str(item.get("id", f"node-{ordinal}")); node_id = "summary." + _slug(raw_id)
        if node_id in seen: node_id = f"{node_id}.{ordinal}"
        seen.add(node_id)
        fields = []
        for key in ("kind", "path", "status"):
            if item.get(key) not in (None, ""): fields.append(f"{key}={item.get(key)}")
        metrics = item.get("metrics")
        if metrics not in (None, {}, []): fields.append(f"metrics={metrics}")
        nodes.append(Node(id=node_id, kind=NodeKind.PARAGRAPH, title=str(item.get("title") or raw_id), content="; ".join(fields) or "Structural summary node.", status="imported", metadata={"summary_node_id": raw_id, "adapter": "omega_summary_fractal_t", "edge_semantics_promoted": False}))
    return DocumentIR(meta=DocumentMeta(title=f"Fractal summary — {root}", template="github-system-report"), nodes=tuple(nodes), provenance={"adapter": "omega_summary_fractal_t", "cache_fingerprint": str(payload.get("cache_fingerprint", "")), "summary_edges": list(payload.get("edges", ())), "boundary": "summary edges preserved as metadata, not promoted to proof/dependency edges"})


def github_snapshot_to_document(snapshot: Mapping[str, Any]) -> DocumentIR:
    """Compile an already-authorized normalized GitHub snapshot; performs no network access."""
    repo = str(snapshot.get("repository", snapshot.get("full_name", "repository")))
    sources: list[Source] = []
    nodes: list[Node] = [Node(id="gh.root", kind=NodeKind.SECTION, title=f"GitHub system report: {repo}", content="", status="imported")]
    for index, pr in enumerate(snapshot.get("pull_requests", ()), start=1):
        pr_number = pr.get("number", index); source_id = f"github.pr.{pr_number}"; url = str(pr.get("url", ""))
        if url: sources.append(Source(id=source_id, citation=f"GitHub PR #{pr_number}", locator=url))
        nodes.append(Node(id=f"gh.pr.{_slug(str(pr_number))}", kind=NodeKind.PARAGRAPH, title=str(pr.get("title", f"PR #{pr_number}")), content=f"state={pr.get('state', 'unknown')}; draft={pr.get('draft', 'unknown')}; head={pr.get('head_sha', '')}", status="imported", sources=(source_id,) if url else (), metadata={"adapter": "github_snapshot", "record_type": "pull_request"}))
    for index, item in enumerate(snapshot.get("files", ()), start=1):
        path = str(item.get("path", item.get("filename", f"file-{index}")))
        nodes.append(Node(id=f"gh.file.{index}", kind=NodeKind.PARAGRAPH, title=path, content=f"status={item.get('status', 'observed')}; additions={item.get('additions', '')}; deletions={item.get('deletions', '')}", status="imported", metadata={"adapter": "github_snapshot", "record_type": "file", "path": path}))
    return DocumentIR(meta=DocumentMeta(title=f"GitHub report — {repo}", template="github-system-report"), nodes=tuple(nodes), sources=tuple(sources), provenance={"adapter": "github_snapshot", "repository": repo, "boundary": "repository state is provenance/engineering evidence, not scientific truth"})


def merge_results(doc: DocumentIR, results: Mapping[str, Any]) -> DocumentIR:
    merged = dict(doc.results); merged.update({str(k): v for k, v in results.items()})
    return replace(doc, results=merged)
