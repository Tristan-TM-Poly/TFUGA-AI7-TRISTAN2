"""Ω-LATEX-T∞ — evidence-bound scientific document compiler."""

from .models import DocumentIR, DocumentMeta, Node, NodeKind, Source, SymbolSpec
from .compiler import BuildArtifact, DocumentCompiler
from .audit import AuditFinding, AuditReport, audit_document
from .bibliography import BibliographyError, CitationEntry, attach_bibliography, bibliography_report, entries_to_sources, parse_bibtex
from .cache_index import CacheIndexError, build_cache_index, cache_shard, write_sharded_index
from .covariance import CovarianceError, covariance_ledger, propagate_jacobian, propagate_linear, quadratic_variance
from .delta import node_hash, semantic_delta
from .evidence import evidence_matrix
from .figure_backends import FigureBackendError, figure_backend_manifest, render_svg, svg_receipt
from .figure_ir import FigureIRError, figure_manifest, render_figure_ir, validate_figure_ir
from .incremental import FragmentCache, fragment_cache_key, rebuild_plan
from .math_ir import Dimension, DimensionError, MathIRError, infer_dimension, parse_unit, render_math
from .metadata_receipts import MetadataReceiptError, metadata_receipt, metadata_receipt_report, normalize_doi
from .metadocument import metadocument_graph
from .notation import notation_registry, notation_rename_plan
from .projection import project_depth, project_depths
from .proof_lineage import ProofLineageError, proof_lineage
from .repo_universe import RepoUniverseError, repository_inventory_to_universe
from .review_queue import metadocument_review_queue
from .source_fragments import SourceFragmentError, SourceFragmentReceipt, extract_text_fragment, source_fragment_report, validate_receipt as validate_source_fragment_receipt
from .theorem_bundle import theorem_bundle, write_theorem_bundle
from .uncertainty import Measurement, UncertaintyError, propagate_independent, render_result_latex, uncertainty_ledger
from .universe import UniverseManifestError, build_universe, normalize_universe_manifest, universe_plan
from .verifier_receipts import VerifierReceipt, VerifierReceiptError, matching_receipt, statement_sha256, verifier_receipt_report

__all__=[
    "AuditFinding","AuditReport","BibliographyError","BuildArtifact","CacheIndexError","CitationEntry","CovarianceError","Dimension","DimensionError","DocumentCompiler","DocumentIR","DocumentMeta","FigureBackendError","FigureIRError","FragmentCache","MathIRError","Measurement","MetadataReceiptError","Node","NodeKind","ProofLineageError","RepoUniverseError","Source","SourceFragmentError","SourceFragmentReceipt","SymbolSpec","UncertaintyError","UniverseManifestError","VerifierReceipt","VerifierReceiptError",
    "attach_bibliography","audit_document","bibliography_report","build_cache_index","build_universe","cache_shard","covariance_ledger","entries_to_sources","evidence_matrix","extract_text_fragment","figure_backend_manifest","figure_manifest","fragment_cache_key","infer_dimension","matching_receipt","metadata_receipt","metadata_receipt_report","metadocument_graph","metadocument_review_queue","node_hash","normalize_doi","normalize_universe_manifest","notation_registry","notation_rename_plan","parse_bibtex","parse_unit","project_depth","project_depths","proof_lineage","propagate_independent","propagate_jacobian","propagate_linear","quadratic_variance","rebuild_plan","render_figure_ir","render_math","render_result_latex","render_svg","repository_inventory_to_universe","semantic_delta","source_fragment_report","statement_sha256","svg_receipt","theorem_bundle","uncertainty_ledger","universe_plan","validate_figure_ir","validate_source_fragment_receipt","verifier_receipt_report","write_sharded_index","write_theorem_bundle"
]

__version__="1.0.0"
