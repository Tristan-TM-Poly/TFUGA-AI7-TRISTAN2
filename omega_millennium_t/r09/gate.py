"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.9."""

from .audit import audit_promotion_gate
from .compiler import compile_promotion_gate
from .model import BUNDLE_SCHEMA, DESTINATIONS, PROMOTION_STATUSES

__all__ = [
    "BUNDLE_SCHEMA",
    "DESTINATIONS",
    "PROMOTION_STATUSES",
    "audit_promotion_gate",
    "compile_promotion_gate",
]
