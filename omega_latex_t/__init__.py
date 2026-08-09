"""Ω-LATEX-T∞ — evidence-bound scientific document compiler."""

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source, SymbolSpec
from .compiler import BuildArtifact, DocumentCompiler
from .audit import AuditFinding, AuditReport, audit_document
from .bibliography import BibliographyError, CitationEntry, attach_bibliography, bibliography_report, entries_to_sources, parse_bibtex
from .delta import node_hash, semantic_delta
from .evidence import evidence_matrix
from .figure_ir import FigureIRError, figure_manifest, render_figure_ir, validate_figure_ir
from .incremental import FragmentCache, fragment_cache_key, rebuild_plan
from .math_ir import Dimension, DimensionError, MathIRError, infer_dimension, parse_unit, render_math
from .metadocument import metadocument_graph
from .notation import notation_registry, notation_rename_plan
from .projection import project_depth, project_depths
from .theorem_bundle import theorem_bundle, write_theorem_bundle
from .uncertainty import Measurement, UncertaintyError, propagate_independent, render_result_latex, uncertainty_ledger
from .universe import UniverseManifestError, build_universe, normalize_universe_manifest, universe_plan
from .verifier_receipts import VerifierReceipt, VerifierReceiptError, matching_receipt, statement_sha256, verifier_receipt_report

__all__=["AuditFinding","AuditReport","BibliographyError","BuildArtifact","CitationEntry","Dimension","DimensionError","DocumentCompiler","DocumentIR","DocumentMeta","FigureIRError","FragmentCache","MathIRError","Measurement","Node","NodeKind","Source","SymbolSpec","UncertaintyError","UniverseManifestError","VerifierReceipt","VerifierReceiptError","attach_bibliography","audit_document","bibliography_report","build_universe","entries_to_sources","evidence_matrix","figure_manifest","fragment_cache_key","infer_dimension","matching_receipt","metadocument_graph","node_hash","normalize_universe_manifest","notation_registry","notation_rename_plan","parse_bibtex","parse_unit","project_depth","project_depths","propagate_independent","rebuild_plan","render_figure_ir","render_math","render_result_latex","semantic_delta","statement_sha256","theorem_bundle","uncertainty_ledger","universe_plan","validate_figure_ir","verifier_receipt_report","write_theorem_bundle"]

__version__="0.8.0"
