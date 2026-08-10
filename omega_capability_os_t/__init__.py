"""Ω-CAPABILITY-OS-T∞: deterministic capability planning, health and OAK receipts."""

from .core import Capability, Intent, make_evidence_receipt, outcome_record, plan, suggest_fallback, validate_registry

__all__ = ["Capability", "Intent", "plan", "suggest_fallback", "validate_registry", "make_evidence_receipt", "outcome_record"]
__version__ = "0.1.0"
