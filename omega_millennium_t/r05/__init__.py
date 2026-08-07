"""Ω-PROBLEM-ATLAS-T∞ R0.5 identity and alias graph.

R0.5 preserves source records, separates aliases from mathematical identity,
and permits merges only through exact statement/signature agreement or an
explicit evidence-backed decision receipt. Fuzzy similarity never merges.
"""

from .identity_graph import (
    DECISION_SCHEMA,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    audit_identity_graph,
    compile_identity_graph,
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

__version__ = "0.5.0"
