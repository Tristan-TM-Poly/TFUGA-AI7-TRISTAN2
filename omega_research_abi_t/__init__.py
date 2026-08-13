"""Ω-UNIVERSAL-RESEARCH-ABI-T∞ R0.1→R0.2.

A small typed interoperability kernel for Tristan research systems.
"""

from .core import (
    GRAPH_KINDS,
    SCHEMA_VERSION,
    Envelope,
    GraphEdge,
    InvariantCheck,
    ObjectRef,
    TransformationReceipt,
    canonical_json,
    stable_digest,
)
from .graphs import ResearchGraphKernel
from .receipts import ReceiptError, issue_receipt, validate_receipt
from .ledger import GENESIS_HASH, ResearchTransitionLedger, TransitionLedgerEntry
from .github_memory_bridge import (
    GITHUB_MEMORY_R07_BOUNDARY,
    PR_LLMT_MEASUREMENT_KIND_BY_FINDING,
    PR_LLMT_R01_BOUNDARY,
    adapt_llmt_federation,
    adapt_pr_llmt_findings,
    adapt_pr_llmt_inspection_overlay,
    adapt_pr_llmt_inspection_plan,
    adapt_pr_llmt_measurement_requests,
    adapt_residual_artifact_spec,
    adapt_reuse_outcome,
    adapt_supersession_report,
    compile_pr_llmt_measurement_requests,
    issue_pr_llmt_inspection_receipt,
    issue_pr_llmt_measurement_request_receipt,
)
from .measurement_allocation import (
    MEASUREMENT_ALLOCATION_POLICY,
    MEASUREMENT_ALLOCATION_SCHEMA,
    PR445_OPPORTUNITY_REQUIRED_FIELDS,
    PR449_VOC_REQUIRED_FIELDS,
    adapt_pr_llmt_measurement_allocation,
    compile_pr_llmt_measurement_allocation,
    issue_pr_llmt_measurement_allocation_receipt,
)
from .github_measurement_bridge import (
    STRUCTURAL_MEASUREMENT_SCHEMA,
    TARGET_FILEGRAPH_SCHEMA,
    adapt_pr_llmt_structural_measurements,
    issue_pr_llmt_reconstruction_blob_measurement_receipt,
)
from .compiler import ResearchABICompiler

__all__ = [
    "GRAPH_KINDS",
    "SCHEMA_VERSION",
    "Envelope",
    "GraphEdge",
    "InvariantCheck",
    "ObjectRef",
    "TransformationReceipt",
    "ResearchGraphKernel",
    "ResearchABICompiler",
    "ReceiptError",
    "issue_receipt",
    "validate_receipt",
    "canonical_json",
    "stable_digest",
    "GENESIS_HASH",
    "ResearchTransitionLedger",
    "TransitionLedgerEntry",
    "GITHUB_MEMORY_R07_BOUNDARY",
    "PR_LLMT_R01_BOUNDARY",
    "PR_LLMT_MEASUREMENT_KIND_BY_FINDING",
    "adapt_llmt_federation",
    "adapt_pr_llmt_findings",
    "adapt_pr_llmt_inspection_overlay",
    "adapt_pr_llmt_inspection_plan",
    "adapt_pr_llmt_measurement_requests",
    "adapt_residual_artifact_spec",
    "adapt_reuse_outcome",
    "adapt_supersession_report",
    "compile_pr_llmt_measurement_requests",
    "issue_pr_llmt_inspection_receipt",
    "issue_pr_llmt_measurement_request_receipt",
    "MEASUREMENT_ALLOCATION_POLICY",
    "MEASUREMENT_ALLOCATION_SCHEMA",
    "PR445_OPPORTUNITY_REQUIRED_FIELDS",
    "PR449_VOC_REQUIRED_FIELDS",
    "adapt_pr_llmt_measurement_allocation",
    "compile_pr_llmt_measurement_allocation",
    "issue_pr_llmt_measurement_allocation_receipt",
    "STRUCTURAL_MEASUREMENT_SCHEMA",
    "TARGET_FILEGRAPH_SCHEMA",
    "adapt_pr_llmt_structural_measurements",
    "issue_pr_llmt_reconstruction_blob_measurement_receipt",
]
