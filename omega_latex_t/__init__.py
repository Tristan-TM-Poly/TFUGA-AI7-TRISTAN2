"""Ω-LATEX-T∞ — evidence-bound document compiler."""

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source, SymbolSpec
from .compiler import BuildArtifact, DocumentCompiler
from .audit import AuditFinding, AuditReport, audit_document
from .adapters import github_snapshot_to_document, markdown_to_document, merge_results, summary_bundle_to_document
from .delta import node_hash, semantic_delta

__all__ = [
    "AuditFinding", "AuditReport", "BuildArtifact", "DocumentCompiler",
    "DocumentIR", "DocumentMeta", "Node", "NodeKind", "Source", "SymbolSpec",
    "audit_document", "github_snapshot_to_document", "markdown_to_document",
    "merge_results", "summary_bundle_to_document", "node_hash", "semantic_delta",
]

__version__ = "0.2.0"
