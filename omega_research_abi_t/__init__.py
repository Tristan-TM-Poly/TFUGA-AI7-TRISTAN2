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
    adapt_llmt_federation,
    adapt_residual_artifact_spec,
    adapt_reuse_outcome,
    adapt_supersession_report,
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
    "adapt_llmt_federation",
    "adapt_residual_artifact_spec",
    "adapt_reuse_outcome",
    "adapt_supersession_report",
]
