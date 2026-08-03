"""Ω-PROBLEM-ATLAS-T∞ R0.8 evidence-updated routing.

R0.8 reconstructs routing priorities from an append-only, hash-chained event
ledger. Scores are operational priorities, never probabilities of mathematical
truth, and M− negative knowledge remains immutable.
"""

from .routing import (
    EVENT_RULES,
    EVENT_SCHEMA,
    audit_routing_campaign,
    compile_routing_campaign,
)

__all__ = [
    "EVENT_RULES",
    "EVENT_SCHEMA",
    "audit_routing_campaign",
    "compile_routing_campaign",
]

__version__ = "0.8.0"
