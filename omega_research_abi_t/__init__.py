"""Ω-UNIVERSAL-RESEARCH-ABI-T∞ R0.2 core reconstruction.

A small typed interoperability kernel for Tristan research systems.
Reconstructed on current main from PR #448 without inheriting the historical
GitHub-memory stack. The memory bridge remains explicitly HOLD until its own
canonical reconstruction is qualified.
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
from .compiler import ResearchABICompiler

GITHUB_MEMORY_BRIDGE_STATUS = "HOLD_UNTIL_CANONICAL_MEMORY_RECONSTRUCTION"

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
    "GITHUB_MEMORY_BRIDGE_STATUS",
]
