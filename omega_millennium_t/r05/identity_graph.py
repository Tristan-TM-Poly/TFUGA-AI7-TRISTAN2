"""Public API for Ω-PROBLEM-ATLAS-T∞ R0.5."""

from .audit import audit_identity_graph
from .compiler import compile_identity_graph
from .model import (
    DECISION_SCHEMA,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    normalize_statement,
    normalize_text,
    statement_fingerprint,
    structural_signature,
)

__all__ = [
    "DECISION_SCHEMA",
    "MANIFEST_SCHEMA",
    "REPORT_SCHEMA",
    "audit_identity_graph",
    "compile_identity_graph",
    "normalize_statement",
    "normalize_text",
    "statement_fingerprint",
    "structural_signature",
]
