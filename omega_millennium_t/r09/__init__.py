"""Ω-PROBLEM-ATLAS-T∞ R0.9 publication, novelty, prize and IP gate.

R0.9 is a fail-closed, dry-run-only compiler. It prepares auditable promotion
bundles but never publishes, submits, files, discloses or claims recognition.
"""

from .gate import (
    BUNDLE_SCHEMA,
    DESTINATIONS,
    PROMOTION_STATUSES,
    audit_promotion_gate,
    compile_promotion_gate,
)

__all__ = [
    "BUNDLE_SCHEMA",
    "DESTINATIONS",
    "PROMOTION_STATUSES",
    "audit_promotion_gate",
    "compile_promotion_gate",
]

__version__ = "0.9.0"
