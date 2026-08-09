"""Ω-LATEX-T∞ — evidence-bound document compiler."""

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source, SymbolSpec
from .compiler import BuildArtifact, DocumentCompiler
from .audit import AuditFinding, AuditReport, audit_document

__all__ = [
    "AuditFinding", "AuditReport", "BuildArtifact", "DocumentCompiler",
    "DocumentIR", "DocumentMeta", "Node", "NodeKind", "Source", "SymbolSpec",
    "audit_document",
]

__version__ = "0.1.0"
