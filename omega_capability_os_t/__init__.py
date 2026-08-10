"""Ω-CAPABILITY-OS-T∞: deterministic capability planning, execution receipts and health learning."""

from .bridge import WorkUnitBridge, compile_workunit, workunit_from_mapping
from .core import Capability, Intent, make_evidence_receipt, outcome_record, plan, suggest_fallback, validate_registry
from .runtime import CapabilityRuntime, HandlerResult, learn_health

__all__ = [
    "Capability",
    "Intent",
    "plan",
    "suggest_fallback",
    "validate_registry",
    "make_evidence_receipt",
    "outcome_record",
    "WorkUnitBridge",
    "compile_workunit",
    "workunit_from_mapping",
    "CapabilityRuntime",
    "HandlerResult",
    "learn_health",
]
__version__ = "0.2.0"
