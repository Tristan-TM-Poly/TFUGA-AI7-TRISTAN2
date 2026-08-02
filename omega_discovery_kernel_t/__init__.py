"""Ω-DISCOVERY-KERNEL-T∞ public API.

The package closes the workflow loop between HyperKnowledge claims and
Generator Discovery candidates. It records typed events and OAK transitions;
it does not certify causal laws or authorize irreversible actions.
"""
from .demo import build_raman_closed_loop
from .events import DiscoveryEvent, EVENT_TYPES, OAK_STATUSES, canonical_json, stable_id
from .kernel import (
    DiscoveryLedger,
    KernelAudit,
    KernelFinding,
    claim_events_from_cell,
    generator_event_from_morph_ir,
    result_event_to_evidence_record,
)

__all__ = [
    "DiscoveryEvent",
    "DiscoveryLedger",
    "EVENT_TYPES",
    "KernelAudit",
    "KernelFinding",
    "OAK_STATUSES",
    "build_raman_closed_loop",
    "canonical_json",
    "claim_events_from_cell",
    "generator_event_from_morph_ir",
    "result_event_to_evidence_record",
    "stable_id",
]

__version__ = "0.1.0"
