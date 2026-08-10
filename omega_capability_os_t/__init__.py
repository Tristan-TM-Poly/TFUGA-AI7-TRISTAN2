"""Ω-CAPABILITY-OS-T∞: capability planning, bounded execution and external receipts."""

from .bridge import WorkUnitBridge, compile_workunit, workunit_from_mapping
from .chatmem import (
    ChatMemCheckpointManifest,
    chatmem_bootstrap_intent,
    chatmem_capabilities,
    chatmem_checkpoint_intent,
    chatmem_external_bindings,
    checkpoint_gate_handler,
    default_chatmem_bootstrap_values,
)
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
    "ChatMemCheckpointManifest",
    "chatmem_capabilities",
    "chatmem_external_bindings",
    "chatmem_bootstrap_intent",
    "chatmem_checkpoint_intent",
    "checkpoint_gate_handler",
    "default_chatmem_bootstrap_values",
]
__version__ = "0.4.0"
