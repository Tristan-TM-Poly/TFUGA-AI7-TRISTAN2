"""Ω-ASM-T∞ — OAK-safe assembly optimization and evidence laboratory."""

from .analysis import analyze, cvcd_signature, dependency_graph
from .backends import emit_dot_u64, supported_variants
from .benchmark import BenchmarkStats, machine_manifest, relative_ratio, summarize_samples
from .cost_model import StaticCostProfile, get_static_cost_profile, static_cost_profiles
from .counters import (
    DEFAULT_PERF_EVENTS,
    HARDWARE_PERF_EVENTS,
    PerfCounter,
    PerfParseResult,
    build_p5_report,
    derive_counter_metrics,
    parse_perf_stat_csv,
    requested_perf_events,
)
from .formal import (
    build_equivalence_obligation,
    build_p7_certificate,
    evaluate_expr,
    exhaustive_verify,
    normalize_equivalence_spec,
    normalize_expr,
    obligation_id,
    parse_solver_status,
)
from .ir import dot_u64_block_program, program_from_dict, validate_program
from .microarch import (
    CacheDescriptor,
    cache_descriptors,
    file_sha256,
    microarchitecture_manifest,
    normalize_architecture,
    parse_size_bytes,
    toolchain_manifest,
)
from .oak import oak_report
from .replication import (
    ReplicationGroup,
    aggregate_p5_reports,
    canonical_machine_identity,
    machine_fingerprint,
    validate_p5_replication_input,
)
from .search import estimate_builtin_candidates, pareto_front

__all__ = [
    "BenchmarkStats",
    "CacheDescriptor",
    "DEFAULT_PERF_EVENTS",
    "HARDWARE_PERF_EVENTS",
    "PerfCounter",
    "PerfParseResult",
    "ReplicationGroup",
    "StaticCostProfile",
    "aggregate_p5_reports",
    "analyze",
    "build_equivalence_obligation",
    "build_p5_report",
    "build_p7_certificate",
    "cache_descriptors",
    "canonical_machine_identity",
    "cvcd_signature",
    "dependency_graph",
    "derive_counter_metrics",
    "dot_u64_block_program",
    "emit_dot_u64",
    "estimate_builtin_candidates",
    "evaluate_expr",
    "exhaustive_verify",
    "file_sha256",
    "get_static_cost_profile",
    "machine_fingerprint",
    "machine_manifest",
    "microarchitecture_manifest",
    "normalize_architecture",
    "normalize_equivalence_spec",
    "normalize_expr",
    "oak_report",
    "obligation_id",
    "pareto_front",
    "parse_perf_stat_csv",
    "parse_size_bytes",
    "parse_solver_status",
    "program_from_dict",
    "relative_ratio",
    "requested_perf_events",
    "static_cost_profiles",
    "summarize_samples",
    "supported_variants",
    "toolchain_manifest",
    "validate_p5_replication_input",
    "validate_program",
]

__version__ = "0.6.0"
