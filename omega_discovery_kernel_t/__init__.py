"""Ω-DISCOVERY-KERNEL-T∞ public API.

R0.2 closes the workflow loop between HyperKnowledge claims and Generator
Discovery candidates, adds an Ω64 event catalog, universal identities,
unit-aware uncertainty records, and a disk-backed frontier capable of tens of
thousands of events without loading the graph in memory.  It does not certify
causal laws or authorize irreversible actions.
"""
from .catalog import (
    EVENT_CATALOG,
    EVENT_FAMILIES,
    EVENT_TYPES,
    EventTypeSpec,
    catalog_manifest,
    event_spec,
)
from .demo import build_raman_closed_loop
from .events import DiscoveryEvent, OAK_STATUSES, canonical_json, stable_id
from .identity import AliasRecord, IdentityRegistry, UniversalIdentity, content_digest
from .kernel import (
    CORE_LOOP_EVENT_TYPES,
    DiscoveryLedger,
    KernelAudit,
    KernelFinding,
    claim_events_from_cell,
    generator_event_from_morph_ir,
    result_event_to_evidence_record,
)
from .quantity import (
    CalibrationReference,
    Quantity,
    QuantityVector,
    compatible_units,
    convert_value,
    quantities_to_event_fields,
    unit_catalog_manifest,
)
from .streaming import (
    AdaptiveFrontierConfig,
    FrontierCheckpoint,
    FrontierExperimentConfig,
    FrontierTelemetry,
    StreamingDiscoveryLedger,
    run_frontier_experiment,
    synthetic_closed_loop_stream,
)

__all__ = [
    "AdaptiveFrontierConfig",
    "AliasRecord",
    "CORE_LOOP_EVENT_TYPES",
    "CalibrationReference",
    "DiscoveryEvent",
    "DiscoveryLedger",
    "EVENT_CATALOG",
    "EVENT_FAMILIES",
    "EVENT_TYPES",
    "EventTypeSpec",
    "FrontierCheckpoint",
    "FrontierExperimentConfig",
    "FrontierTelemetry",
    "IdentityRegistry",
    "KernelAudit",
    "KernelFinding",
    "OAK_STATUSES",
    "Quantity",
    "QuantityVector",
    "StreamingDiscoveryLedger",
    "UniversalIdentity",
    "build_raman_closed_loop",
    "canonical_json",
    "catalog_manifest",
    "claim_events_from_cell",
    "compatible_units",
    "content_digest",
    "convert_value",
    "event_spec",
    "generator_event_from_morph_ir",
    "quantities_to_event_fields",
    "result_event_to_evidence_record",
    "run_frontier_experiment",
    "stable_id",
    "synthetic_closed_loop_stream",
    "unit_catalog_manifest",
]

__version__ = "0.2.0"
