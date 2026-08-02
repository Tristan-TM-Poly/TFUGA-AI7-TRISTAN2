"""Ω-DISCOVERY-KERNEL-T∞ public API.

R0.3 closes the workflow loop between HyperKnowledge claims and Generator
Discovery candidates, adds an Ω64 event catalog, 36 benchmark families,
universal identities, unit-aware uncertainty records, adaptive 50k and
one-million-event frontiers, and a 50,100 logical GitHub-addition planner. It
does not certify causal laws or authorize irreversible actions.
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
from .factory import (
    BENCHMARK_FAMILIES,
    BenchmarkCase,
    BenchmarkFamily,
    KnowledgeFrontierTargets,
    benchmark_registry_manifest,
    iter_benchmark_cases,
    iter_knowledge_frontier_additions,
    plan_knowledge_frontier,
)
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
from .million_frontier import (
    COMPACT_CORE_EVENT_TYPES,
    CompactEventRecord,
    CompactMillionFrontier,
    ForcedInterruption,
    MillionFrontierConfig,
    MillionTelemetry,
    SaturationRecord,
    run_forced_resume_million_frontier,
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
    "BENCHMARK_FAMILIES",
    "BenchmarkCase",
    "BenchmarkFamily",
    "COMPACT_CORE_EVENT_TYPES",
    "CORE_LOOP_EVENT_TYPES",
    "CalibrationReference",
    "CompactEventRecord",
    "CompactMillionFrontier",
    "DiscoveryEvent",
    "DiscoveryLedger",
    "EVENT_CATALOG",
    "EVENT_FAMILIES",
    "EVENT_TYPES",
    "EventTypeSpec",
    "ForcedInterruption",
    "FrontierCheckpoint",
    "FrontierExperimentConfig",
    "FrontierTelemetry",
    "IdentityRegistry",
    "KernelAudit",
    "KernelFinding",
    "KnowledgeFrontierTargets",
    "MillionFrontierConfig",
    "MillionTelemetry",
    "OAK_STATUSES",
    "Quantity",
    "QuantityVector",
    "SaturationRecord",
    "StreamingDiscoveryLedger",
    "UniversalIdentity",
    "benchmark_registry_manifest",
    "build_raman_closed_loop",
    "canonical_json",
    "catalog_manifest",
    "claim_events_from_cell",
    "compatible_units",
    "content_digest",
    "convert_value",
    "event_spec",
    "generator_event_from_morph_ir",
    "iter_benchmark_cases",
    "iter_knowledge_frontier_additions",
    "plan_knowledge_frontier",
    "quantities_to_event_fields",
    "result_event_to_evidence_record",
    "run_forced_resume_million_frontier",
    "run_frontier_experiment",
    "stable_id",
    "synthetic_closed_loop_stream",
    "unit_catalog_manifest",
]

__version__ = "0.3.0"
