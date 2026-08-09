"""Ω-LATEX-T∞ — evidence-bound scientific document compiler."""

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source, SymbolSpec
from .compiler import BuildArtifact, DocumentCompiler
from .audit import AuditFinding, AuditReport, audit_document
from .adapters import (
    github_pr_event_to_document,
    github_pr_event_to_snapshot,
    github_snapshot_to_document,
    markdown_to_document,
    merge_results,
    summary_bundle_to_document,
)
from .delta import node_hash, semantic_delta
from .evidence import evidence_matrix
from .incremental import FragmentCache, fragment_cache_key, rebuild_plan
from .math_ir import Dimension, DimensionError, MathIRError, infer_dimension, parse_unit, render_math
from .notation import notation_registry, notation_rename_plan
from .projection import project_depth, project_depths
from .theorem_bundle import theorem_bundle, write_theorem_bundle

__all__ = [
    "AuditFinding",
    "AuditReport",
    "BuildArtifact",
    "Dimension",
    "DimensionError",
    "DocumentCompiler",
    "DocumentIR",
    "DocumentMeta",
    "FragmentCache",
    "MathIRError",
    "Node",
    "NodeKind",
    "Source",
    "SymbolSpec",
    "audit_document",
    "evidence_matrix",
    "fragment_cache_key",
    "github_pr_event_to_document",
    "github_pr_event_to_snapshot",
    "github_snapshot_to_document",
    "infer_dimension",
    "markdown_to_document",
    "merge_results",
    "node_hash",
    "notation_registry",
    "notation_rename_plan",
    "parse_unit",
    "project_depth",
    "project_depths",
    "rebuild_plan",
    "render_math",
    "semantic_delta",
    "summary_bundle_to_document",
    "theorem_bundle",
    "write_theorem_bundle",
]

__version__ = "0.5.0"
