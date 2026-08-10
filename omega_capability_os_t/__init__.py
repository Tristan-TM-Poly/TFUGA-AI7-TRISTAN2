"""Ω-CAPABILITY-OS-T∞: capability planning, bounded execution and external receipts."""

from .bridge import WorkUnitBridge, compile_workunit, workunit_from_mapping
from .core import Capability, Intent, make_evidence_receipt, outcome_record, plan, suggest_fallback, validate_registry
from .external import (
    ExternalActionReceipt,
    ExternalActionRequest,
    ExternalBinding,
    ExternalResolver,
    load_external_bindings,
    make_external_request,
    validate_external_bindings,
    validate_external_receipt,
)
from .runtime import ActionRequired, CapabilityRuntime, HandlerResult, learn_health

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
    "ActionRequired",
    "CapabilityRuntime",
    "HandlerResult",
    "learn_health",
    "ExternalBinding",
    "ExternalActionRequest",
    "ExternalActionReceipt",
    "ExternalResolver",
    "load_external_bindings",
    "make_external_request",
    "validate_external_bindings",
    "validate_external_receipt",
]
__version__ = "0.3.0"
