"""Ω-UNIVERSAL-RESEARCH-ABI-T∞ R0.1.

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
]
